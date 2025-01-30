from django.db.models import Q
from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from employer.models import Employee, RollCall, WorkShiftPlan, EmployeeRequest, Workplace
from employer.serializers import AttendeesSerializer, AbsenteesSerializer
from employer.utilities import subtract_times, calculate_roll_call_query_duration, calculate_daily_shift_duration, total_minute_to_hour_and_minutes, send_response_file, \
    REPORT_PERMISSION_STR, calculate_hourly_request_duration, calculate_daily_request_duration, DailyStatus, DASHBOARD_PERMISSION_STR
from employer.views import DATE_FORMAT_STR, check_user_permission, VIEW_PERMISSION_STR


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, DASHBOARD_PERMISSION_STR)
def get_employer_dashboard(request, **kwargs):
    shifts = WorkShiftPlan.objects.filter(date=now()).values_list("work_shift", flat=True)
    employees = Employee.objects.filter(work_shift__in=shifts).distinct()
    # todo write aggregations for these queries
    today_roll_calls = RollCall.objects.filter(arrival__lte=now(),
                                               # fixme for test purposes
                                               #  date=now(),
                                               employee__in=employees).distinct("employee")
    attendees = today_roll_calls.filter(departure__isnull=True, )
    absentees = today_roll_calls.filter(departure__isnull=False, )

    attendees_ser = AttendeesSerializer(attendees, many=True)
    absentees_ser = AbsenteesSerializer(absentees, many=True)
    return Response({"attendees": attendees_ser.data, "absentees": absentees_ser.data, "attendees_count": attendees.count(), "absentees_count": absentees.count(),
                     "total_employees_count": employees.count()}, status=status.HTTP_200_OK)


def calculate_employee_requests(employee_requests, plans):
    hourly_missions = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_MISSION)
    daily_missions = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_MISSION)
    missions = calculate_hourly_request_duration(hourly_missions) + calculate_daily_request_duration(daily_missions, plans)

    hourly_earned_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_EARNED_LEAVE)
    daily_earned_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_EARNED_LEAVE)
    earned_leave = calculate_daily_request_duration(daily_earned_leave, plans) + calculate_hourly_request_duration(hourly_earned_leave)

    hourly_sick_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_SICK_LEAVE)
    daily_sick_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_SICK_LEAVE)
    sick_leave = calculate_daily_request_duration(daily_sick_leave, plans) + calculate_hourly_request_duration(hourly_sick_leave)

    hourly_unpaid_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_UNPAID_LEAVE)
    daily_unpaid_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_UNPAID_LEAVE)
    unpaid_leave = calculate_hourly_request_duration(hourly_unpaid_leave) + calculate_daily_request_duration(daily_unpaid_leave, plans)

    return {"missions": missions, "earned_leave": earned_leave, "sick_leave": sick_leave, "unpaid_leave": unpaid_leave, }


def calculate_arrival_and_departure(arrival, departure, period_start, period_end):
    this_early_arrival = this_late_arrival = this_early_departure = this_late_departure = 0
    if arrival > period_start:
        this_late_arrival = subtract_times(period_start, arrival)

    elif arrival < period_start:
        this_early_arrival = subtract_times(arrival, period_start)

    if departure < period_end:
        this_early_departure = subtract_times(arrival, period_end)

    if departure > period_end:
        this_late_departure = subtract_times(period_end, departure)
    return this_early_arrival, this_late_arrival, this_early_departure, this_late_departure


def one_period_one_roll_call(plan, arrival, departure, daily_status=None):
    if daily_status is None:
        daily_status = DailyStatus(plan)
        daily_status.add_attend(subtract_times(arrival, departure))

    if arrival > plan.first_period_start:
        daily_status.late_arrival = subtract_times(plan.first_period_start, arrival)
        if plan.permitted_delay is not None and plan.permitted_delay > 0:
            if plan.permitted_delay > daily_status.late_arrival:
                daily_status.late_arrival = 0

    elif arrival < plan.first_period_start:
        daily_status.early_arrival = subtract_times(arrival, plan.first_period_start)

    if departure < plan.first_period_end:
        daily_status.early_departure = subtract_times(arrival, plan.first_period_end)
        if plan.permitted_acceleration is not None and plan.permitted_acceleration > 0:
            if daily_status.early_departure < plan.permitted_acceleration:
                daily_status.early_departure = 0

    if departure > plan.first_period_end:
        daily_status.late_departure = subtract_times(plan.first_period_end, departure)
        if daily_status.late_arrival > 0:
            if plan.floating_time is not None and plan.floating_time > 0:
                f = min(plan.floating_time, daily_status.late_arrival)
                if daily_status.late_departure > f:
                    daily_status.late_departure -= f
                    daily_status.late_arrival -= f
                else:
                    daily_status.late_arrival -= daily_status.late_departure
                    daily_status.late_departure = 0

    # --------------------------------------------------------------------------------
    if daily_status.early_arrival > 0:
        if plan.beginning_overtime is not None and plan.beginning_overtime > 0:
            b = min(daily_status.early_arrival, plan.beginning_overtime)
            daily_status.overtime += b
            if daily_status.early_arrival - b > 0:
                daily_status.burned_out["beginning_overtime"] = daily_status.early_arrival - b
    if daily_status.late_arrival > 0:
        daily_status.absent += daily_status.late_arrival

    if daily_status.early_departure > 0:
        daily_status.absent += daily_status.late_arrival
    if daily_status.late_departure > 0:
        if plan.second_period_start is not None:
            if plan.middle_overtime is not None and plan.middle_overtime > 0:
                o = min(daily_status.late_departure, plan.middle_overtime)
                daily_status.overtime += o
                if daily_status.late_departure - o > 0:
                    daily_status.burned_out["middle_overtime"] = daily_status.late_departure - o

        elif plan.ending_overtime is not None and plan.ending_overtime > 0:
            e = min(daily_status.late_departure, plan.ending_overtime)
            daily_status.overtime += e
            if daily_status.late_departure - e > 0:
                daily_status.burned_out["ending_overtime"] = daily_status.late_departure - e
    daily_status.absent = daily_status.absent
    daily_status.overtime = daily_status.overtime

    return daily_status


def one_period_multiple_roll_calls(plan, roll_calls, ):
    roll_calls = roll_calls.order_by('arrival')
    folded_arrival = roll_calls[0].arrival
    folded_departure = roll_calls.last().departure
    folded_attend = 0
    for roll_call in roll_calls:
        folded_attend += subtract_times(roll_call.arrival, roll_call.departure)
    stat = DailyStatus()
    stat.date = plan.date
    stat.attend = folded_attend
    stat = one_period_one_roll_call(plan, folded_arrival, folded_departure, stat)
    stat.absent += (subtract_times(folded_arrival, folded_departure, ) - folded_attend)
    return stat


def two_period_multiple_roll_calls(plan: WorkShiftPlan, roll_calls, ):
    stat = DailyStatus(plan)
    stat.attend = calculate_roll_call_query_duration(roll_calls)
    first_period_roll_calls = roll_calls.filter(arrival__lte=plan.first_period_end)
    if first_period_roll_calls:
        first_period_roll_calls = roll_calls.order_by('arrival')
        folded_arrival = first_period_roll_calls[0].arrival
        folded_departure = first_period_roll_calls.last().departure
        folded_attend = 0
        for roll_call in first_period_roll_calls:
            folded_attend += subtract_times(roll_call.arrival, roll_call.departure)
        stat.absent += (subtract_times(folded_arrival, folded_departure, ) - folded_attend)
        # stat.early_arrival, stat.late_arrival, stat.early_departure, stat.late_departure = calculate_arrival_and_departure(
        #     folded_arrival, folded_departure, plan.first_period_start, plan.first_period_end)
        stat.first_period_arrival_and_departure(*calculate_arrival_and_departure(folded_arrival, folded_departure, plan.first_period_start, plan.first_period_end))

    else:
        stat.absent += subtract_times(plan.first_period_start, plan.first_period_end)

    second_period_roll_calls = roll_calls.exclude(first_period_roll_calls)
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


def simple_attend(plan, date_str, plan_roll_calls, burned_out, absent, overtime):
    this_overtime = this_absent = this_early_arrival = this_late_arrival = this_early_departure = this_late_departure = 0
    for roll_call in plan_roll_calls:
        if roll_call.arrival < plan.first_period_end:
            roll_call_result = calculate_arrival_and_departure(roll_call.arrival, roll_call.departure, plan.first_period_start, plan.first_period_end)
        else:
            roll_call_result = calculate_arrival_and_departure(roll_call.arrival, roll_call.departure, plan.second_period_start, plan.second_period_end)

        this_early_arrival += roll_call_result[0]
        this_late_arrival += roll_call_result[1]
        this_early_departure += roll_call_result[2]
        this_late_departure += roll_call_result[3]

    # ----------------------------------------------------------------#}
    if plan.permitted_delay is not None and plan.permitted_delay > 0:
        if plan.permitted_delay > this_late_arrival:
            this_late_arrival = 0

    if plan.permitted_acceleration is not None and plan.permitted_acceleration > 0:
        if this_early_departure < plan.permitted_acceleration:
            this_early_departure = 0

    if this_late_arrival > 0:
        if plan.floating_time is not None and plan.floating_time > 0:
            f = min(plan.floating_time, this_late_arrival)
            if this_late_departure > f:
                this_late_departure -= f
                this_late_arrival -= f
            else:
                this_late_arrival -= this_late_departure
                this_late_departure = 0

    # --------------------------------------------------------------------------------
    if this_early_arrival > 0:
        if plan.beginning_overtime is not None and plan.beginning_overtime > 0:
            b = min(this_early_arrival, plan.beginning_overtime)
            this_overtime += b
            if this_early_arrival - b > 0:
                burned_out[date_str + "_beginning_overtime"] = this_early_arrival - b
    if this_late_arrival > 0:
        this_absent += this_late_arrival

    if this_early_departure > 0:
        this_absent += this_late_arrival
    if this_late_departure > 0:
        if plan.second_period_start is not None:
            if plan.middle_overtime is not None and plan.middle_overtime > 0:
                o = min(this_late_departure, plan.middle_overtime)
                this_overtime += o
                if this_late_departure - o > 0:
                    burned_out[date_str + "_middle_overtime"] = this_late_departure - o

        elif plan.ending_overtime is not None and plan.ending_overtime > 0:
            e = min(this_late_departure, plan.ending_overtime)
            this_overtime += e
            if this_late_departure - e > 0:
                burned_out[date_str + "_ending_overtime"] = this_late_departure - e
    absent[date_str] = this_absent
    overtime[date_str] = this_overtime


# def create_employee_report(employee):
#     absent = {}
#     attend = {}
#     overtime = {}
#     burned_out = {}
#     mission = {}
#     earned = {}
#     sick = {}
#     unpaid = {}
#     # todo add date in [start, end] filter parameter
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
#         # fixme filter requests by date
#         #  todays_e_requests = employee_requests.filter(Q(date=plan.date) | Q(date__lte=plan.date, end_date__gte=plan.date))
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
#                     # todo if plan have second shift
#                     #  if roll_call.arrival > plan.first_period_end => second shift
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

def create_employee_report(employee: Employee):
    absent = {}
    attend = {}
    overtime = {}
    burned_out = {}
    # todo add date in [start, end] filter parameter
    employee_requests = employee.employeerequest_set.filter(status=EmployeeRequest.STATUS_APPROVED)
    roll_calls = employee.rollcall_set.filter(~(Q(departure__isnull=True) | Q(arrival__isnull=True)), )
    plans = employee.work_shift.workshiftplan_set.all()
    result = calculate_employee_requests(employee_requests, plans)
    # ---------------------------------------------
    for plan in plans:
        date_str = plan.date.strftime(DATE_FORMAT_STR)
        plan_roll_calls = roll_calls.filter(date=plan.date).order_by("arrival")
        timetable = plan_roll_calls.values_list("arrival", "departure", )
        print(timetable)
        # fixme filter requests by date
        #  todays_e_requests = employee_requests.filter(Q(date=plan.date) | Q(date__lte=plan.date, end_date__gte=plan.date))
        today_hourly_employee_requests = employee_requests.filter(category__in=[EmployeeRequest.CATEGORY_HOURLY_MISSION,
                                                                                EmployeeRequest.CATEGORY_HOURLY_EARNED_LEAVE,
                                                                                EmployeeRequest.CATEGORY_HOURLY_UNPAID_LEAVE,
                                                                                EmployeeRequest.CATEGORY_HOURLY_SICK_LEAVE,
                                                                                ])

        if plan.plan_type == WorkShiftPlan.SIMPLE_PLAN_TYPE:
            if plan_roll_calls.exists():
                if today_hourly_employee_requests.exists():
                    # complex_attend()
                    pass
                else:
                    simple_attend(plan, date_str, plan_roll_calls, burned_out, absent, overtime)

            else:
                absent[date_str] = calculate_daily_shift_duration(plan)
        elif plan.plan_type == WorkShiftPlan.FLOATING_PLAN_TYPE:
            if plan_roll_calls.exists():
                total_minutes = calculate_roll_call_query_duration(plan_roll_calls)
                attend[date_str] = total_minutes
                if total_minutes > plan.daily_duty_duration:
                    this_overtime = total_minutes - plan.daily_duty_duration
                    if plan.daily_overtime_limit is not None and plan.daily_overtime_limit > 0:
                        overtime[date_str] = min(this_overtime, plan.daily_overtime_limit)
                        if this_overtime > plan.daily_overtime_limit:
                            burned_out[date_str] = this_overtime - plan.daily_overtime_limit

            else:
                absent[date_str] = plan.daily_duty_duration
        else:
            return Response({"msg": "WorkShiftPlan PLAN_TYPE is not acceptable"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    result.update({
        "total_attend": total_minute_to_hour_and_minutes(calculate_roll_call_query_duration(roll_calls)[2]),
        "total_absent": sum(absent.values()),
        "total_overtime": sum(overtime.values()),
        "total_burned_out": sum(burned_out.values()),
        "days_attended": roll_calls.distinct("date").count(),
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
        result.append(create_employee_report(employee))
    return result


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def report_employees_function(request, **kwargs):
    result = filter_employees_and_their_requests(request, **kwargs)
    return Response(result, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def get_employees_function_report_excel(request, **kwargs):
    # fixme this is placebo...
    #  workplaces_list = filter_employees_and_their_requests(request)
    workplaces_list = Workplace.objects.all()
    data = [["name", "city", "address", "radius", "latitude", "longitude", "BSSID"]]
    for fin in workplaces_list:
        data.append([fin.name, fin.city, fin.address, fin.radius, fin.latitude, fin.longitude, fin.BSSID])
    return send_response_file(data, 'employees_function_report')


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def get_employee_report(request, oid, **kwargs):
    employee = get_object_or_404(Employee, id=oid, employer_id=kwargs["employer"])
    report = create_employee_report(employee)
    return Response(report, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def report_personnel_leave(request, **kwargs):
    # todo filter to month and year
    employees = Employee.objects.filter(employer_id=request.user.id)
    for employee in employees:
        monthly = {}
        yearly = {}
        total_monthly = total_yearly = balance_monthly = balance_yearly = 0

        employee_requests = EmployeeRequest.objects.filter(
            Q(category=EmployeeRequest.CATEGORY_DAILY_EARNED_LEAVE) |
            Q(category=EmployeeRequest.CATEGORY_DAILY_SICK_LEAVE) |
            Q(category=EmployeeRequest.CATEGORY_HOURLY_SICK_LEAVE) |
            Q(category=EmployeeRequest.CATEGORY_DAILY_UNPAID_LEAVE) |
            Q(category=EmployeeRequest.CATEGORY_HOURLY_UNPAID_LEAVE) |
            Q(category=EmployeeRequest.CATEGORY_HOURLY_EARNED_LEAVE),
            employee=employee, action=EmployeeRequest.STATUS_APPROVED)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def report_employee_traffic(request, **kwargs):
    emp = get_object_or_404(Employee, id=request.data.get("employee_id"), employer_id=request.user.id)
    report = create_employee_report(emp)
    return Response(report, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def get_employee_traffic_report_excel(request, **kwargs):
    # fixme this is placebo...
    #  workplaces_list = filter_employees_and_their_requests(request)
    workplaces_list = Workplace.objects.all()
    data = [["name", "city", "address", "radius", "latitude", "longitude", "BSSID"]]
    for fin in workplaces_list:
        data.append([fin.name, fin.city, fin.address, fin.radius, fin.latitude, fin.longitude, fin.BSSID])
    return send_response_file(data, 'employees_function_report')


def filter_employee_and_lives(request):
    emp = get_object_or_404(Employee, id=request.data.get("employee_id"), employer_id=request.user.id)
    report = create_employee_report(emp)
    return report


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def report_employee_leave(request, **kwargs):
    report = filter_employee_and_lives(request)
    return Response(report, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def get_employee_leave_report_excel(request, **kwargs):
    # fixme this is placebo...
    #  workplaces_list = filter_employee_and_lives(request)(request)
    workplaces_list = Workplace.objects.all()
    data = [["name", "city", "address", "radius", "latitude", "longitude", "BSSID"]]
    for fin in workplaces_list:
        data.append([fin.name, fin.city, fin.address, fin.radius, fin.latitude, fin.longitude, fin.BSSID])
    return send_response_file(data, 'employees_function_report')


def filter_project_traffic(request):
    emp = get_object_or_404(Employee, id=request.data.get("employee_id"), employer_id=request.user.id)
    report = create_employee_report(emp)
    return report


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, REPORT_PERMISSION_STR)
def report_project_traffic(request, **kwargs):
    report = filter_employee_and_lives(request)
    return Response(report, status=status.HTTP_200_OK)
