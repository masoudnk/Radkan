from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet
from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from employer.models import Employee, RollCall, WorkShiftPlan, EmployeeRequest
from employer.serializers import AttendeesSerializer, AbsenteesSerializer, DailyStatusSerializer
from employer.utilities import subtract_times, calculate_roll_call_query_duration, calculate_daily_shift_duration, total_minute_to_hour_and_minutes, send_response_file, \
    REPORT_PERMISSION_STR, calculate_hourly_request_duration, calculate_daily_request_duration, DASHBOARD_PERMISSION_STR, positive_only
from employer.views import DATE_FORMAT_STR, check_user_permission, VIEW_PERMISSION_STR


class DailyStatus:
    middle_overtime = attend = overtime = absent = 0
    first_period_early_arrival = first_period_late_arrival = first_period_early_departure = first_period_late_departure = 0
    second_period_early_arrival = second_period_late_arrival = second_period_early_departure = second_period_late_departure = 0

    def __init__(self, plan: WorkShiftPlan):
        self.plan: WorkShiftPlan = plan
        self.burned_out = {}

    def deduct_absence_from_overtimes(self):
        if self.absent > 0 and self.first_period_early_arrival + self.first_period_late_departure + self.second_period_early_arrival + self.second_period_late_departure > 0:
            if self.first_period_early_arrival > 0:
                if self.first_period_early_arrival >= self.absent:
                    self.first_period_early_arrival -= self.absent
                    self.absent = 0
                else:
                    self.absent -= self.first_period_early_arrival
                    self.first_period_early_arrival = 0
            elif self.first_period_late_departure > 0:
                if self.first_period_late_departure >= self.absent:
                    self.first_period_late_departure -= self.absent
                    self.absent = 0
                else:
                    self.absent -= self.first_period_late_departure
                    self.first_period_late_departure = 0
            elif self.second_period_early_arrival > 0:
                if self.second_period_early_arrival >= self.absent:
                    self.second_period_early_arrival -= self.absent
                    self.absent = 0
                else:
                    self.absent -= self.second_period_early_arrival
                    self.second_period_early_arrival = 0
            else:
                if self.second_period_late_departure >= self.absent:
                    self.second_period_late_departure -= self.absent
                    self.absent = 0
                else:
                    self.absent -= self.second_period_late_departure
                    self.second_period_late_departure = 0

    def get_date(self):
        return self.plan.date.strftime(DATE_FORMAT_STR)

    def get_weekday(self):
        return self.plan.date.jweekday()

    @positive_only
    def add_attend(self, attended):
        self.attend += attended

    @positive_only
    def add_absent(self, absented):
        self.absent += absented

    @positive_only
    def deduct_absent(self, accepted_time):
        self.absent -= accepted_time

    @positive_only
    def first_period_arrival_and_departure(self, early_arrival, late_arrival, early_departure, late_departure):
        self.first_period_early_arrival += early_arrival
        self.first_period_late_arrival += late_arrival
        self.first_period_early_departure += early_departure
        self.first_period_late_departure += late_departure

    @positive_only
    def second_period_arrival_and_departure(self, early_arrival, late_arrival, early_departure, late_departure):
        self.second_period_early_arrival += early_arrival
        self.second_period_late_arrival += late_arrival
        self.second_period_early_departure += early_departure
        self.second_period_late_departure += late_departure

    @positive_only
    def match_floating_time(self, late_departure, late_arrival):
        if late_departure > 0 and late_arrival > 0:
            if self.plan.floating_time is not None and self.plan.floating_time > 0:
                floating_time = min(self.plan.floating_time, late_arrival)
                if late_departure > floating_time:
                    late_departure -= floating_time
                    late_arrival -= floating_time
                else:
                    late_arrival -= late_departure
                    late_departure = 0
        return late_departure, late_arrival

    def recalculate_floating_time(self):
        self.first_period_late_departure, self.first_period_late_arrival = self.match_floating_time(self.first_period_late_departure, self.first_period_late_arrival)
        self.second_period_late_departure, self.second_period_late_arrival = self.match_floating_time(self.second_period_late_departure, self.second_period_late_arrival)

    def calculate_ending_overtime(self):
        if self.second_period_late_departure > 0 and self.plan.ending_overtime is not None and self.plan.ending_overtime > 0:
            ending_overtime = min(self.second_period_late_departure, self.plan.ending_overtime)
            self.overtime += ending_overtime
            if self.second_period_late_departure - ending_overtime > 0:
                self.burned_out["ending_overtime"] = self.second_period_late_departure - ending_overtime

    def calculate_beginning_overtime(self):
        if self.first_period_early_arrival > 0:
            if self.plan.beginning_overtime is not None and self.plan.beginning_overtime > 0:
                beginning_overtime = min(self.first_period_early_arrival, self.plan.beginning_overtime)
                self.overtime += beginning_overtime
                if self.first_period_early_arrival - beginning_overtime > 0:
                    self.burned_out["beginning_overtime"] = self.first_period_early_arrival - beginning_overtime

    def calculate_middle_overtime(self):
        if self.plan.second_period_start is not None:
            if self.plan.middle_overtime is not None and self.plan.middle_overtime > 0:
                combined = self.first_period_late_departure + self.second_period_early_arrival
                middle_overtime = min(combined, self.plan.middle_overtime)
                self.overtime += middle_overtime
                burn_out = combined - middle_overtime
                if burn_out > 0:
                    self.burned_out["middle_overtime"] = burn_out

    def calculate_all_overtimes(self):
        self.recalculate_floating_time()
        self.calculate_ending_overtime()
        self.calculate_beginning_overtime()
        self.calculate_middle_overtime()
    # def calculate_second_period_middle_overtime(self):
    #     if self.second_period_early_arrival > 0 and self.plan.middle_overtime is not None and self.plan.middle_overtime > 0:
    #         if self.middle_overtime > 0:
    #             acceptable_overtime = self.plan.middle_overtime - self.middle_overtime
    #         else:
    #             acceptable_overtime = self.plan.middle_overtime
    #         self.middle_overtime += min(self.second_period_early_arrival, acceptable_overtime)


class ReportCrucial:
    def __init__(self, employee: Employee, kwargs):
        self.date_period = [kwargs["start"], kwargs["end"]]
        self.requests = employee.employeerequest_set.filter(Q(date__in=self.date_period) | Q(end_date__in=self.date_period), status=EmployeeRequest.STATUS_APPROVED, )
        self.roll_calls = employee.rollcall_set.filter(~(Q(departure__isnull=True) | Q(arrival__isnull=True)), date__in=self.date_period).order_by("date")
        self.plans = employee.work_shift.workshiftplan_set.all().order_by("date")
        self.imperfect_roll_calls = employee.rollcall_set.filter(Q(departure__isnull=True) | Q(arrival__isnull=True), date__in=self.date_period).order_by("date")


def calculate_total_roll_calls_and_traffics(roll_calls: QuerySet[RollCall], traffics: QuerySet[EmployeeRequest]):
    calculated_roll_calls = []
    arrives = []
    departs = []
    employee = roll_calls[0].employee
    date = roll_calls[0].date
    for r in roll_calls:
        if r.arrival:
            arrives.append(r.arrival)
        elif r.departure:
            departs.append(r.departure)
        else:
            raise ValidationError("roll call has no arrival or departure")
    for t in traffics:
        if t.manual_traffic_type == EmployeeRequest.Login:
            arrives.append(t.time)
        elif t.manual_traffic_type == EmployeeRequest.Logout:
            departs.append(t.time)
        else:
            raise ValidationError("manual traffic type is not acceptable")
    arrives.sort(reverse=True)
    departs.sort(reverse=True)

    for a in arrives:
        nearest_departure = last_duration = None
        for d in departs:
            if a > d:
                break
            duration = subtract_times(a, d)
            if last_duration is None or duration < last_duration:
                last_duration = duration
                nearest_departure = d
        if nearest_departure is not None:
            calculated_roll_calls.append(RollCall(
                employee=employee,
                date=date,
                arrival=a,
                departure=nearest_departure,
            ))
            departs.remove(nearest_departure)
    return calculated_roll_calls


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, DASHBOARD_PERMISSION_STR)
def get_employer_dashboard(request, **kwargs):
    shifts = WorkShiftPlan.objects.filter(date=now()).values_list("work_shift", flat=True)
    employees = Employee.objects.filter(work_shift__in=shifts).distinct()
    today_roll_calls = RollCall.objects.filter(arrival__lte=now(), date=now(), employee__in=employees, departure__isnull=True, ).distinct("employee")
    attendees = []
    absentees = []
    for emp in employees:
        if today_roll_calls.filter(employee=emp).exists():
            attendees.append(emp)
        else:
            absentees.append(emp)
    # attendees = today_roll_calls.filter(departure__isnull=True, )
    # absentees = today_roll_calls.filter(departure__isnull=False, )

    attendees_ser = AttendeesSerializer(attendees, many=True)
    absentees_ser = AbsenteesSerializer(absentees, many=True)
    return Response({"attendees": attendees_ser.data, "absentees": absentees_ser.data, "attendees_count": len(attendees), "absentees_count": len(absentees),
                     "total_employees_count": employees.count()}, status=status.HTTP_200_OK)


def calculate_employee_requests(employee_requests, plans, kwargs):
    hourly_missions = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_MISSION)
    daily_missions = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_MISSION)
    missions = calculate_hourly_request_duration(hourly_missions) + calculate_daily_request_duration(daily_missions, plans, kwargs)

    hourly_earned_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_EARNED_LEAVE)
    daily_earned_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_EARNED_LEAVE)
    earned_leave = calculate_daily_request_duration(daily_earned_leave, plans, kwargs) + calculate_hourly_request_duration(hourly_earned_leave)

    hourly_sick_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_SICK_LEAVE)
    daily_sick_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_SICK_LEAVE)
    sick_leave = calculate_daily_request_duration(daily_sick_leave, plans, kwargs) + calculate_hourly_request_duration(hourly_sick_leave)

    hourly_unpaid_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_UNPAID_LEAVE)
    daily_unpaid_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_UNPAID_LEAVE)
    unpaid_leave = calculate_hourly_request_duration(hourly_unpaid_leave) + calculate_daily_request_duration(daily_unpaid_leave, plans, kwargs)

    return {"missions": total_minute_to_hour_and_minutes(missions), "earned_leave": total_minute_to_hour_and_minutes(earned_leave),
            "sick_leave": total_minute_to_hour_and_minutes(sick_leave), "unpaid_leave": total_minute_to_hour_and_minutes(unpaid_leave),
            "integers": {"missions": missions, "earned_leave": earned_leave, "sick_leave": sick_leave, "unpaid_leave": unpaid_leave, }}


def calculate_arrival_and_departure(arrival, departure, period_start, period_end):
    this_early_arrival = this_late_arrival = this_early_departure = this_late_departure = 0
    if arrival > period_start:
        this_late_arrival = subtract_times(period_start, arrival)

    elif arrival < period_start:
        this_early_arrival = subtract_times(arrival, period_start)

    if departure < period_end:
        this_early_departure = subtract_times(arrival, period_end)

    elif departure > period_end:
        this_late_departure = subtract_times(period_end, departure)
    return this_early_arrival, this_late_arrival, this_early_departure, this_late_departure


def one_period_one_roll_call(plan, arrival, departure, daily_status=None):
    if daily_status is None:
        daily_status = DailyStatus(plan)
        daily_status.add_attend(subtract_times(arrival, departure))

    if arrival > plan.first_period_start:
        daily_status.first_period_late_arrival = subtract_times(plan.first_period_start, arrival)
        if plan.permitted_delay is not None and plan.permitted_delay > 0:
            if plan.permitted_delay > daily_status.first_period_late_arrival:
                daily_status.first_period_late_arrival = 0

    elif arrival < plan.first_period_start:
        daily_status.first_period_early_arrival = subtract_times(arrival, plan.first_period_start)

    if departure < plan.first_period_end:
        daily_status.first_period_early_departure = subtract_times(departure, plan.first_period_end)
        if plan.permitted_acceleration is not None and plan.permitted_acceleration > 0:
            if daily_status.first_period_early_departure < plan.permitted_acceleration:
                daily_status.first_period_early_departure = 0

    if departure > plan.first_period_end:
        daily_status.first_period_late_departure = subtract_times(plan.first_period_end, departure)
        if daily_status.first_period_late_arrival > 0:
            if plan.floating_time is not None and plan.floating_time > 0:
                f = min(plan.floating_time, daily_status.first_period_late_arrival)
                if daily_status.first_period_late_departure > f:
                    daily_status.first_period_late_departure -= f
                    daily_status.first_period_late_arrival -= f
                else:
                    daily_status.first_period_late_arrival -= daily_status.first_period_late_departure
                    daily_status.first_period_late_departure = 0

    # --------------------------------------------------------------------------------
    daily_status.deduct_absence_from_overtimes()
    # --------------------------------------------------------------------------------
    if daily_status.first_period_early_arrival > 0:
        if plan.beginning_overtime is not None and plan.beginning_overtime > 0:
            b = min(daily_status.first_period_early_arrival, plan.beginning_overtime)
            daily_status.overtime += b
            if daily_status.first_period_early_arrival - b > 0:
                daily_status.burned_out["pre_shift_overtime"] = daily_status.first_period_early_arrival - b
    if daily_status.first_period_late_arrival > 0:
        daily_status.absent += daily_status.first_period_late_arrival

    if daily_status.first_period_early_departure > 0:
        daily_status.absent += daily_status.first_period_early_departure
    if daily_status.first_period_late_departure > 0:
        if plan.second_period_start is not None:
            if plan.middle_overtime is not None and plan.middle_overtime > 0:
                o = min(daily_status.first_period_late_departure, plan.middle_overtime)
                daily_status.overtime += o
                if daily_status.first_period_late_departure - o > 0:
                    daily_status.burned_out["middle_shift_overtime"] = daily_status.first_period_late_departure - o

        elif plan.ending_overtime is not None and plan.ending_overtime > 0:
            e = min(daily_status.first_period_late_departure, plan.ending_overtime)
            daily_status.overtime += e
            if daily_status.first_period_late_departure - e > 0:
                daily_status.burned_out["past_shift_overtime"] = daily_status.first_period_late_departure - e
    return daily_status


def one_period_multiple_roll_calls(plan, roll_calls, ):
    roll_calls = roll_calls.order_by('arrival')
    folded_arrival = roll_calls[0].arrival
    folded_departure = roll_calls.last().departure
    folded_attend = 0
    for roll_call in roll_calls:
        folded_attend += subtract_times(roll_call.arrival, roll_call.departure)
    stat = DailyStatus(plan)
    stat.add_attend(folded_attend)
    stat.add_absent(subtract_times(folded_arrival, folded_departure, ) - folded_attend)
    stat = one_period_one_roll_call(plan, folded_arrival, folded_departure, stat)
    return stat


def two_period_multiple_roll_calls(plan: WorkShiftPlan, roll_calls, ):
    stat = DailyStatus(plan)
    stat.add_attend(calculate_roll_call_query_duration(roll_calls)[2])
    first_period_roll_calls = roll_calls.filter(arrival__lte=plan.first_period_end)
    if first_period_roll_calls:
        first_period_roll_calls = first_period_roll_calls.order_by('arrival')
        folded_arrival = first_period_roll_calls[0].arrival
        folded_departure = first_period_roll_calls.last().departure
        folded_attend = 0
        for roll_call in first_period_roll_calls:
            folded_attend += subtract_times(roll_call.arrival, roll_call.departure)
        stat.add_absent(subtract_times(folded_arrival, folded_departure, ) - folded_attend)
        # print(stat.absent)
        stat.first_period_arrival_and_departure(*calculate_arrival_and_departure(folded_arrival, folded_departure, plan.first_period_start, plan.first_period_end))

    else:
        stat.absent += subtract_times(plan.first_period_start, plan.first_period_end)
    second_period_roll_calls = roll_calls.filter(arrival__gte=plan.first_period_end)
    # second_period_roll_calls = roll_calls.exclude(id__in=first_period_roll_calls.values_list('id', flat=True))
    if second_period_roll_calls:
        second_period_roll_calls = second_period_roll_calls.order_by('arrival')
        folded_arrival = second_period_roll_calls[0].arrival
        folded_departure = second_period_roll_calls.last().departure
        folded_attend = 0
        for roll_call in second_period_roll_calls:
            folded_attend += subtract_times(roll_call.arrival, roll_call.departure)
        stat.absent += (subtract_times(folded_arrival, folded_departure, ) - folded_attend)
        stat.second_period_arrival_and_departure(*calculate_arrival_and_departure(folded_arrival, folded_departure, plan.second_period_start, plan.second_period_end))
    else:
        stat.absent += subtract_times(plan.second_period_start, plan.second_period_end)
    # --------------------------------------------------------------------------------
    if stat.first_period_late_arrival + stat.second_period_late_arrival > 0:
        if plan.permitted_delay is not None and plan.permitted_delay > 0:
            if plan.permitted_delay > stat.first_period_late_arrival + stat.second_period_late_arrival:
                stat.first_period_late_arrival = stat.second_period_late_arrival = 0
    if stat.first_period_early_departure > 0 and stat.first_period_early_arrival > 0:
        if plan.permitted_acceleration is not None and plan.permitted_acceleration > 0:
            if stat.first_period_early_departure < plan.permitted_acceleration:
                stat.first_period_early_arrival -= stat.first_period_early_departure
                stat.first_period_early_departure = 0
    if stat.second_period_early_departure > 0 and stat.second_period_early_arrival > 0:
        if plan.permitted_acceleration is not None and plan.permitted_acceleration > 0:
            if stat.second_period_early_departure < plan.permitted_acceleration:
                stat.second_period_early_arrival -= stat.second_period_early_departure
                stat.second_period_early_departure = 0

    # if stat.first_period_late_departure >0 and  stat.first_period_late_arrival>0:
    #         if stat.plan.floating_time is not None and stat.plan.floating_time > 0:
    #             floating_time = min(stat.plan.floating_time, stat.first_period_late_arrival)
    #             if stat.first_period_late_departure > floating_time:
    #                 stat.first_period_late_departure -= floating_time
    #                 stat.first_period_late_arrival -= floating_time
    #             else:
    #                 stat.first_period_late_arrival -= stat.first_period_late_departure
    #                 stat.first_period_late_departure = 0

    stat.calculate_all_overtimes()
    stat.add_absent(stat.first_period_late_arrival + stat.second_period_late_arrival + stat.first_period_early_departure + stat.second_period_early_departure)
    return stat


# def simple_attend(plan, date_str, plan_roll_calls, burned_out, absent, overtime):
#     this_overtime = this_absent = this_early_arrival = this_late_arrival = this_early_departure = this_late_departure = 0
#     for roll_call in plan_roll_calls:
#         if roll_call.arrival < plan.first_period_end:
#             roll_call_result = calculate_arrival_and_departure(roll_call.arrival, roll_call.departure, plan.first_period_start, plan.first_period_end)
#         else:
#             roll_call_result = calculate_arrival_and_departure(roll_call.arrival, roll_call.departure, plan.second_period_start, plan.second_period_end)
#
#         this_early_arrival += roll_call_result[0]
#         this_late_arrival += roll_call_result[1]
#         this_early_departure += roll_call_result[2]
#         this_late_departure += roll_call_result[3]
#
#     # ----------------------------------------------------------------#}
#     if plan.permitted_delay is not None and plan.permitted_delay > 0:
#         if plan.permitted_delay > this_late_arrival:
#             this_late_arrival = 0
#
#     if plan.permitted_acceleration is not None and plan.permitted_acceleration > 0:
#         if this_early_departure < plan.permitted_acceleration:
#             this_early_departure = 0
#
#     if this_late_arrival > 0:
#         if plan.floating_time is not None and plan.floating_time > 0:
#             f = min(plan.floating_time, this_late_arrival)
#             if this_late_departure > f:
#                 this_late_departure -= f
#                 this_late_arrival -= f
#             else:
#                 this_late_arrival -= this_late_departure
#                 this_late_departure = 0
#
#     # --------------------------------------------------------------------------------
#     if this_early_arrival > 0:
#         if plan.beginning_overtime is not None and plan.beginning_overtime > 0:
#             b = min(this_early_arrival, plan.beginning_overtime)
#             this_overtime += b
#             if this_early_arrival - b > 0:
#                 burned_out[date_str + "_beginning_overtime"] = this_early_arrival - b
#     if this_late_arrival > 0:
#         this_absent += this_late_arrival
#
#     if this_early_departure > 0:
#         this_absent += this_late_arrival
#     if this_late_departure > 0:
#         if plan.second_period_start is not None:
#             if plan.middle_overtime is not None and plan.middle_overtime > 0:
#                 o = min(this_late_departure, plan.middle_overtime)
#                 this_overtime += o
#                 if this_late_departure - o > 0:
#                     burned_out[date_str + "_middle_overtime"] = this_late_departure - o
#
#         elif plan.ending_overtime is not None and plan.ending_overtime > 0:
#             e = min(this_late_departure, plan.ending_overtime)
#             this_overtime += e
#             if this_late_departure - e > 0:
#                 burned_out[date_str + "_ending_overtime"] = this_late_departure - e
#     absent[date_str] = this_absent
#     overtime[date_str] = this_overtime
# def create_employee_report(employee):
#     absent = {}
#     attend = {}
#     overtime = {}
#     burned_out = {}
#     mission = {}
#     earned = {}
#     sick = {}
#     unpaid = {}
#     roll_calls = RollCall.objects.filter(~(Q(departure__isnull=True) | Q(arrival__isnull=True)), employee_id=employee.id, )
#     employee_requests = employee.employeerequest_set.filter(status=EmployeeRequest.STATUS_APPROVED)
#
#     hourly_missions = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_MISSION)
#     daily_missions = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_MISSION)
#
#     hourly_earned_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_EARNED_LEAVE)
#     daily_earned_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_EARNED_LEAVE)
#
#     hourly_sick_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_SICK_LEAVE)
#     daily_sick_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_SICK_LEAVE)
#
#     hourly_unpaid_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_UNPAID_LEAVE)
#     daily_unpaid_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_UNPAID_LEAVE)
#
#     days_attended = roll_calls.distinct("date").count()
#
#     # ---------------------------------------------
#     plans = employee.work_shift.workshiftplan_set.all()
#     for plan in plans:
#         date_str = plan.date.strftime(DATE_FORMAT_STR)
#         plan_roll_calls = roll_calls.filter(date=plan.date).order_by("arrival")
#         timetable = plan_roll_calls.values_list("arrival", "departure", )
#         print(timetable)
#         todays_e_requests = employee_requests
#
#         if todays_e_requests.exists():
#             for req in todays_e_requests:
#                 if req.category == EmployeeRequest.CATEGORY_DAILY_MISSION:
#                     mission[date_str] = calculate_daily_shift_duration(plan)
#                 elif req.category == EmployeeRequest.CATEGORY_DAILY_EARNED_LEAVE:
#                     earned[date_str] = calculate_daily_shift_duration(plan)
#                 elif req.category == EmployeeRequest.CATEGORY_DAILY_SICK_LEAVE:
#                     sick[date_str] = calculate_daily_shift_duration(plan)
#                 elif req.category == EmployeeRequest.CATEGORY_DAILY_UNPAID_LEAVE:
#                     unpaid[date_str] = calculate_daily_shift_duration(plan)
#                 # create final timetable
#                 # elif req.category in [ EmployeeRequest.CATEGORY_HOURLY_MISSION,
#                 #                        EmployeeRequest.CATEGORY_HOURLY_EARNED_LEAVE,
#                 #                        EmployeeRequest.CATEGORY_HOURLY_UNPAID_LEAVE,
#                 #                        EmployeeRequest.CATEGORY_HOURLY_SICK_LEAVE,
#                 #                        ]:
#                 #     # if req.time < final_roll_call.arrival:
#                 #     #     final_roll_call.arrival = req.time
#                 #     # if req.to_time > final_roll_call.departure:
#                 #     #     final_roll_call.departure = req.to_time
#
#         if plan_roll_calls.exists():
#             total_minutes = calculate_query_duration(plan_roll_calls)
#             attend[date_str] = total_minutes
#
#             if plan.plan_type == WorkShiftPlan.SIMPLE_PLAN_TYPE:
#                 this_overtime = this_absent = this_early_arrival = this_late_arrival = this_early_departure = this_late_departure = 0
#                 for roll_call in plan_roll_calls:
#                     if roll_call.arrival > plan.first_period_start:
#                         this_late_arrival = subtract_times(plan.first_period_start, roll_call.arrival)
#                         if plan.permitted_delay is not None and plan.permitted_delay > 0:
#                             if plan.permitted_delay > this_late_arrival:
#                                 this_late_arrival = 0
#
#                     elif roll_call.arrival < plan.first_period_start:
#                         this_early_arrival = subtract_times(roll_call.arrival, plan.first_period_start)
#
#                     if roll_call.departure < plan.first_period_end:
#                         this_early_departure = subtract_times(roll_call.arrival, plan.first_period_end)
#                         if plan.permitted_acceleration is not None and plan.permitted_acceleration > 0:
#                             if this_early_departure < plan.permitted_acceleration:
#                                 this_early_departure = 0
#
#                     if roll_call.departure > plan.first_period_end:
#                         this_late_departure = subtract_times(plan.first_period_end, roll_call.departure)
#                         if this_late_arrival > 0:
#                             if plan.floating_time is not None and plan.floating_time > 0:
#                                 f = min(plan.floating_time, this_late_arrival)
#                                 if this_late_departure > f:
#                                     this_late_departure -= f
#                                     this_late_arrival -= f
#                                 else:
#                                     this_late_arrival -= this_late_departure
#                                     this_late_departure = 0
#
#                     # --------------------------------------------------------------------------------
#                     if this_early_arrival > 0:
#                         if plan.beginning_overtime is not None and plan.beginning_overtime > 0:
#                             b = min(this_early_arrival, plan.beginning_overtime)
#                             this_overtime += b
#                             if this_early_arrival - b > 0:
#                                 burned_out[date_str + "_beginning_overtime"] = this_early_arrival - b
#                     if this_late_arrival > 0:
#                         this_absent += this_late_arrival
#
#                     if this_early_departure > 0:
#                         this_absent += this_late_arrival
#                     if this_late_departure > 0:
#                         if plan.second_period_start is not None:
#                             if plan.middle_overtime is not None and plan.middle_overtime > 0:
#                                 o = min(this_late_departure, plan.middle_overtime)
#                                 this_overtime += o
#                                 if this_late_departure - o > 0:
#                                     burned_out[date_str + "_middle_overtime"] = this_late_departure - o
#
#                         elif plan.ending_overtime is not None and plan.ending_overtime > 0:
#                             e = min(this_late_departure, plan.ending_overtime)
#                             this_overtime += e
#                             if this_late_departure - e > 0:
#                                 burned_out[date_str + "_ending_overtime"] = this_late_departure - e
#                 absent[date_str] = this_absent
#                 overtime[date_str] = this_overtime
#
#             elif plan.plan_type == WorkShiftPlan.FLOATING_PLAN_TYPE:
#                 if total_minutes > plan.daily_duty_duration:
#                     this_overtime = total_minutes - plan.daily_duty_duration
#                     if plan.daily_overtime_limit is not None and plan.daily_overtime_limit > 0:
#                         overtime[date_str] = min(this_overtime, plan.daily_overtime_limit)
#                         if this_overtime > plan.daily_overtime_limit:
#                             burned_out[date_str] = this_overtime - plan.daily_overtime_limit
#             else:
#                 return Response({"msg": "WorkShiftPlan PLAN_TYPE is not acceptable"}, status=status.HTTP_406_NOT_ACCEPTABLE)
#         else:
#             if plan.plan_type == WorkShiftPlan.SIMPLE_PLAN_TYPE:
#                 # first_duration = (plan.first_period_end.hour * 60 + plan.first_period_end.minute) - (plan.first_period_start.hour * 60 + plan.first_period_start.minute)
#                 # first_duration = subtract_times(plan.first_period_start, plan.first_period_end)
#                 # this_absent = first_duration
#                 # if plan.second_period_start is not None and plan.second_period_end is not None:
#                 #     this_absent += subtract_times(plan.second_period_start, plan.second_period_end)
#                 absent[date_str] = calculate_daily_shift_duration(plan)
#             elif plan.plan_type == WorkShiftPlan.FLOATING_PLAN_TYPE:
#                 absent[date_str] = plan.daily_duty_duration
#             else:
#                 return Response({"msg": "WorkShiftPlan PLAN_TYPE is not acceptable"}, status=status.HTTP_406_NOT_ACCEPTABLE)
#
#     return {
#         "total_attend": total_minute_to_hour_and_minutes(calculate_query_duration(roll_calls)[2]),
#         "total_absent": sum(absent.values()),
#         "total_overtime": sum(overtime.values()),
#         "total_burned_out": sum(burned_out.values()),
#         "total_mission": sum(mission.values()),
#         "total_earned": sum(earned.values()),
#         "total_sick": sum(sick.values()),
#         "total_unpaid": sum(unpaid.values()),
#
#         "days_attended": days_attended,
#         "absent": absent,
#         "attend": attend,
#         "overtime": overtime,
#         "burned_out": burned_out,
#         "mission": mission,
#         "earned": earned,
#         "sick": sick,
#         "unpaid": unpaid,
#     }
def deduct_request_time_from_absense(req: EmployeeRequest, period_start, period_end):
    if req.time < period_start:
        time_start = period_start
    else:
        time_start = req.time
    if req.to_time < period_end:
        time_end = req.to_time
    else:
        time_end = period_end
    return subtract_times(time_start, time_end)


def create_employee_daily_report(plan, plan_roll_calls, hourly_employee_requests):
    if plan.plan_type == WorkShiftPlan.SIMPLE_PLAN_TYPE:
        if plan_roll_calls.exists():
            if plan.second_period_start is None and len(plan_roll_calls) == 1:
                stat = one_period_one_roll_call(plan, plan_roll_calls[0].arrival, plan_roll_calls[0].departure)
            elif plan.second_period_start is None and plan_roll_calls.count() > 1:
                stat = one_period_multiple_roll_calls(plan, plan_roll_calls)
            elif plan.second_period_start is not None:
                stat = two_period_multiple_roll_calls(plan, plan_roll_calls)
            else:
                raise Exception("unhandled plan and roll call situation")

            if hourly_employee_requests.exists():
                for req in hourly_employee_requests:
                    if req.time < plan.first_period_end:
                        req_time = deduct_request_time_from_absense(req, plan.first_period_start, plan.first_period_end)
                    else:
                        req_time = deduct_request_time_from_absense(req, plan.second_period_start, plan.second_period_end)
                    # print(stat.absent)
                    stat.deduct_absent(req_time)
        else:
            stat = DailyStatus(plan)
            stat.add_absent(calculate_daily_shift_duration(plan))
        return stat
    elif plan.plan_type == WorkShiftPlan.FLOATING_PLAN_TYPE:
        stat = DailyStatus(plan)
        if plan_roll_calls.exists():
            total_minutes = calculate_roll_call_query_duration(plan_roll_calls)[2]
            stat.add_attend(total_minutes)
            if total_minutes > plan.daily_duty_duration:
                this_overtime = total_minutes - plan.daily_duty_duration
                if plan.daily_overtime_limit is not None and plan.daily_overtime_limit > 0:
                    stat.overtime += min(this_overtime, plan.daily_overtime_limit)
                    if this_overtime > plan.daily_overtime_limit:
                        stat.burned_out["floating_shift_overtime"] = this_overtime - plan.daily_overtime_limit
            elif total_minutes < plan.daily_duty_duration:
                stat.add_absent(plan.daily_duty_duration - total_minutes)

        else:
            stat.add_absent(plan.daily_duty_duration)
    else:
        raise ValidationError("WorkShiftPlan PLAN_TYPE is not acceptable")
    return stat


def create_employee_timeline_report(employee: Employee, kwargs):
    # employee_requests = employee.employeerequest_set.filter(status=EmployeeRequest.STATUS_APPROVED)
    # roll_calls = employee.rollcall_set.filter(~(Q(departure__isnull=True) | Q(arrival__isnull=True)), )
    # imperfect_roll_calls = employee.rollcall_set.filter(Q(departure__isnull=True) | Q(arrival__isnull=True))
    # plans = employee.work_shift.workshiftplan_set.all().order_by("date")
    report = ReportCrucial(employee, kwargs)
    timetable = []
    for plan in report.plans:
        plan_roll_calls = report.roll_calls.filter(date=plan.date).order_by("arrival")
        plan_traffics = report.requests.filter(date=plan.date, category=EmployeeRequest.CATEGORY_MANUAL_TRAFFIC)
        plan_roll_calls = list(plan_roll_calls).extend(
            calculate_total_roll_calls_and_traffics(report.imperfect_roll_calls.filter(date=plan.date).order_by("arrival"), plan_traffics))
        today_hourly_employee_requests = report.requests.filter(category__in=[EmployeeRequest.CATEGORY_HOURLY_MISSION, EmployeeRequest.CATEGORY_HOURLY_EARNED_LEAVE,
                                                                              EmployeeRequest.CATEGORY_HOURLY_UNPAID_LEAVE, EmployeeRequest.CATEGORY_HOURLY_SICK_LEAVE, ])
        stat = create_employee_daily_report(plan, plan_roll_calls, today_hourly_employee_requests)
        timetable.append(stat)
    return timetable


def create_employee_traffic_report(employee: Employee, kwargs):
    # date_period = [kwargs["start"], kwargs["end"]]
    # employee_requests = employee.employeerequest_set.filter(status=EmployeeRequest.STATUS_APPROVED)
    # roll_calls = employee.rollcall_set.filter(~(Q(departure__isnull=True) | Q(arrival__isnull=True)), date__in=date_period, )
    # plans = employee.work_shift.workshiftplan_set.filter(date__in=date_period).order_by("date")
    report = ReportCrucial(employee, kwargs)
    timetable = []
    for plan in report.plans:
        plan_roll_calls = report.roll_calls.filter(date=plan.date).order_by("arrival")
        today_hourly_employee_requests = report.requests.filter(category__in=[EmployeeRequest.CATEGORY_HOURLY_MISSION, EmployeeRequest.CATEGORY_HOURLY_EARNED_LEAVE,
                                                                              EmployeeRequest.CATEGORY_HOURLY_UNPAID_LEAVE, EmployeeRequest.CATEGORY_HOURLY_SICK_LEAVE, ],
                                                                date=plan.date)
        stat = create_employee_daily_report(plan, plan_roll_calls, today_hourly_employee_requests)
        a = DailyStatusSerializer(stat).data
        a["burned_out"] = sum(stat.burned_out.values())
        b = calculate_employee_requests(today_hourly_employee_requests, report.plans, kwargs)
        b.update(a)
        timetable.append(b)
    return timetable


def create_employee_total_report(employee: Employee, kwargs):
    # date_period = [kwargs["start"], kwargs["end"]]
    absent = {}
    overtime = {}
    burned_out = {}
    report = ReportCrucial(employee, kwargs)
    # employee_requests = employee.employeerequest_set.filter(Q(date__in=date_period) | Q(end_date__in=date_period), status=EmployeeRequest.STATUS_APPROVED, )
    # roll_calls = employee.rollcall_set.filter(~(Q(departure__isnull=True) | Q(arrival__isnull=True)), date__in=date_period).order_by("date")
    # plans = employee.work_shift.workshiftplan_set.filter(date__in=date_period).order_by("date")
    result = {"data": []}
    result.update(calculate_employee_requests(report.requests, report.plans, kwargs))
    # ---------------------------------------------
    timeline = create_employee_timeline_report(employee, kwargs)
    for stat in timeline:
        if stat.absent > 0:
            absent[stat.get_date()] = stat.absent
        if stat.overtime > 0:
            overtime[stat.get_date()] = stat.overtime
        total_burned_out = sum(stat.burned_out.values())
        if total_burned_out > 0:
            burned_out[stat.get_date()] = total_burned_out

    result.update({
        "total_attend": total_minute_to_hour_and_minutes(calculate_roll_call_query_duration(report.roll_calls)[2]),
        "total_absent": total_minute_to_hour_and_minutes(sum(absent.values())),
        "total_overtime": total_minute_to_hour_and_minutes(sum(overtime.values())),
        "total_burned_out": total_minute_to_hour_and_minutes(sum(burned_out.values())),
        "days_attended": report.roll_calls.distinct("date").count(),
        "employee": employee.get_full_name(),
        "employee_id": employee.id,
        # "absent": absent,
        # "attend": attend,
        # "overtime": overtime,
        # "burned_out": burned_out,
    }
    )
    return result


def filter_employees_and_their_requests(request, **kwargs):  # a view request
    employees = Employee.objects.filter(employer_id=kwargs['employer'])
    result = []
    for employee in employees:
        result.append(create_employee_total_report(employee, kwargs))
    return result


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def report_employees_function(request, **kwargs):
    result = filter_employees_and_their_requests(request, **kwargs)
    return Response(result, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def get_employees_function_report_excel(request, **kwargs):
    result = filter_employees_and_their_requests(request, **kwargs)
    cols = ["employee", "total_attend", "total_absent", "total_overtime", "missions", "earned_leave", "sick_leave", "unpaid_leave", "total_burned_out", "days_attended"]
    data = [["نام", "مجموع حضور", "غیبت", "اضافه کار", "ماموریت", "مرخصی استحقاقی", "مرخصی استعلاجی", "مرخصی بی حقوق", "مازاد حضور", "روز کارکرد", ]]
    for row in result:
        data.append([row[key] for key in cols])
    return send_response_file(data, 'employees_function_report')


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def get_employee_report(request, oid, **kwargs):
    employee = get_object_or_404(Employee, id=oid, employer_id=kwargs["employer"])
    report = create_employee_total_report(employee, kwargs)
    return Response(report, status=status.HTTP_200_OK)


def get_leave_requests(employee: Employee, year):
    employee_requests = EmployeeRequest.objects.filter(
        Q(category=EmployeeRequest.CATEGORY_DAILY_SICK_LEAVE) |
        Q(category=EmployeeRequest.CATEGORY_HOURLY_SICK_LEAVE) |
        Q(category=EmployeeRequest.CATEGORY_DAILY_UNPAID_LEAVE) |
        Q(category=EmployeeRequest.CATEGORY_HOURLY_UNPAID_LEAVE) |
        Q(category=EmployeeRequest.CATEGORY_DAILY_EARNED_LEAVE) |
        Q(category=EmployeeRequest.CATEGORY_HOURLY_EARNED_LEAVE),
        employee=employee, status=EmployeeRequest.STATUS_APPROVED,
        date__year=year)
    return employee_requests


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def report_employee_traffic(request, oid, **kwargs):
    # todo filter by date too
    emp = get_object_or_404(Employee, id=oid, employer_id=kwargs.get("employer"))
    report = create_employee_traffic_report(emp, kwargs)
    return Response(report, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def get_employee_traffic_report_excel(request, oid, **kwargs):
    # todo filter by date too
    emp = get_object_or_404(Employee, id=oid, employer_id=kwargs.get("employer"))
    report = create_employee_traffic_report(emp, kwargs)
    cols = ["date", "weekday", "attend", "absent", "earned_leave", "sick_leave", "unpaid_leave", "overtime", "burned_out", "missions"]
    data = [["تاریخ", "روز هفته", "کل حضور", "غیبت", "مرخصی استحقاقی", "مرخصی استعلاجی", "مرخصی بی حقوق", "اضافه کار", "مازاد حضور", "ماموریت", ]]
    for row in report:
        data.append([row[key] for key in cols])
    return send_response_file(data, 'employee_traffic_report')


def filter_employee_and_lives(employee, kwargs):
    # todo filter by type
    plans = employee.work_shift.workshiftplan_set.all().order_by("date")
    yearly = get_leave_requests(employee, kwargs.get("year"))
    monthly = yearly.filter(date__month=kwargs.get("month"))
    monthly_used = sum(calculate_employee_requests(monthly, plans, kwargs)["integers"].values())
    yearly_used = sum(calculate_employee_requests(yearly, plans, kwargs)["integers"].values())
    lp = employee.work_policy.earnedleavepolicy
    if lp:
        lp_m = lp.maximum_hour_per_month * 60 + lp.maximum_minute_per_month
        lp_y = lp.maximum_hour_per_year * 60 + lp.maximum_minute_per_year
    else:
        lp_m = 0
        lp_y = 0
    return {"monthly_used": monthly_used,
            "yearly_used": yearly_used,
            "monthly_count": monthly.count(),
            "yearly_count": yearly.count(),
            "monthly_remained": lp_m,
            "yearly_remained": lp_y
            }


#     return report


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def report_employee_leave(request, oid, **kwargs):
    employee = get_object_or_404(Employee, id=oid, employer_id=kwargs.get("employer"))
    return Response(filter_employee_and_lives(employee, kwargs), status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def report_employees_leave(request, **kwargs):
    # todo filter to month and year
    employees = Employee.objects.filter(employer_id=request.user.id)
    result = []
    for employee in employees:
        row = filter_employee_and_lives(employee, kwargs)
        row.update({"personnel_code": employee.personnel_code, "employee": employee.get_full_name()})
        result.append(row)
    return Response(result, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def get_employees_leave_excel(request, **kwargs):
    # todo filter to month and year
    employees = Employee.objects.filter(employer_id=request.user.id)
    result = [["کد", "نام", "استفاده ماهانه", "استفاده سالانه", "تعداد ماهانه", "تعداد سالانه", "مانده ماهانه", "مانده سالانه", ]]
    cols = ["personnel_code", "employee", "monthly_used", "yearly_used", "monthly_count", "yearly_count", "monthly_remained", "yearly_remained", ]
    for employee in employees:
        data = [employee.personnel_code, employee.get_full_name()]
        row = filter_employee_and_lives(employee, kwargs)
        for key in cols:
            data.append(row[key])
        result.append(data)
    return send_response_file(result, 'personnel_leave')


def filter_project_traffic(request):
    emp = get_object_or_404(Employee, id=request.data.get("employee_id"), employer_id=request.user.id)
    report = create_employee_total_report(emp)
    return report


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def report_project_traffic(request, **kwargs):
    report = filter_employee_and_lives(request)
    return Response(report, status=status.HTTP_200_OK)
