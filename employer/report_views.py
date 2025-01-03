from django.db.models import Q
from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from employer.models import Employee, RollCall, WorkShiftPlan, EmployeeRequest
from employer.serializers import AttendeesSerializer, AbsenteesSerializer
from employer.utilities import subtract_times, calculate_query_duration, calculate_daily_shift_duration
from employer.views import GET_METHOD_STR, DATE_FORMAT_STR


@api_view([GET_METHOD_STR])
def get_employer_dashboard(request):
    shifts = WorkShiftPlan.objects.filter(date=now()).values_list("work_shift", flat=True)
    employees = Employee.objects.filter(work_shift__in=shifts).distinct()
    # todo write aggregations for these queries
    roll_calls = RollCall.objects.filter(date=now(), arrival__lte=now(), departure__isnull=True, employee__in=employees)
    attendees = employees.filter(id__in=roll_calls.values_list("employees", flat=True))
    absentees = employees.exclude(attendees)

    attendees_ser = AttendeesSerializer(attendees, many=True)
    absentees_ser = AbsenteesSerializer(absentees, many=True)
    return Response({"attendees": attendees_ser.data, "absentees": absentees_ser.data, }, status=status.HTTP_200_OK)


@api_view([GET_METHOD_STR])
def report_employees_function(request):
    employees = Employee.objects.filter(employer_id=request.user.id)
    result = []
    for employee in employees:
        absent = {}
        attend = {}
        overtime = {}
        burned_out = {}
        mission = {}
        earned = {}
        sick = {}
        unpaid = {}

        # fixme what shall we do for incomplete roll_calls ?
        roll_calls = RollCall.objects.filter(employee_id=employee.id, departure__isnull=False)
        employee_requests = employee.employeerequest_set.filter(action=EmployeeRequest.ACTION_APPROVED)
        hourly_missions = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_MISSION)
        daily_missions = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_MISSION)
        hourly_earned_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_EARNED_LEAVE)
        daily_earned_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_EARNED_LEAVE)

        hourly_sick_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_SICK_LEAVE)
        daily_sick_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_SICK_LEAVE)

        hourly_unpaid_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_HOURLY_UNPAID_LEAVE)
        daily_unpaid_leave = employee_requests.filter(category=EmployeeRequest.CATEGORY_DAILY_UNPAID_LEAVE)

        days_attended = roll_calls.distinct("date").count()
        hours, minutes, _ = calculate_query_duration(roll_calls)
        # ---------------------------------------------
        plans = employee.work_shift.workshiftplan_set.all()
        for plan in plans:
            date_str = plan.date.strftime(DATE_FORMAT_STR)
            plan_roll_calls = roll_calls.filter(date=plan.date)
            # fixme filter requests by dat
            #  todays_e_requests = employee_requests.filter(Q(date=plan.date) | Q(date__lte=plan.date, end_date__gte=plan.date))
            todays_e_requests = employee_requests

            if todays_e_requests.exists():
                for req in todays_e_requests:
                    if req.category == EmployeeRequest.CATEGORY_DAILY_MISSION:
                        mission[date_str] = calculate_daily_shift_duration(plan)
                    elif req.category == EmployeeRequest.CATEGORY_DAILY_EARNED_LEAVE:
                        earned[date_str] = calculate_daily_shift_duration(plan)
                    elif req.category == EmployeeRequest.CATEGORY_DAILY_SICK_LEAVE:
                        sick[date_str] = calculate_daily_shift_duration(plan)
                    elif req.category == EmployeeRequest.CATEGORY_DAILY_UNPAID_LEAVE:
                        unpaid[date_str] = calculate_daily_shift_duration(plan)

            if plan_roll_calls.exists():
                hours, minutes, total_minutes = calculate_query_duration(plan_roll_calls)
                attend[date_str] = total_minutes

                if plan.plan_type == WorkShiftPlan.SIMPLE_PLAN_TYPE:
                    this_overtime = this_absent = this_early_arrival = this_late_arrival = this_early_departure = this_late_departure = 0
                    for roll_call in plan_roll_calls:
                        # todo if plan have second shift
                        #  if roll_call.arrival > plan.first_period_end => second shift
                        if roll_call.arrival > plan.first_period_start:
                            this_late_arrival = subtract_times(plan.first_period_start, roll_call.arrival)
                            if plan.permitted_delay is not None and plan.permitted_delay > 0:
                                if plan.permitted_delay > this_late_arrival:
                                    this_late_arrival = 0

                        elif roll_call.arrival < plan.first_period_start:
                            this_early_arrival = subtract_times(roll_call.arrival, plan.first_period_start)

                        if roll_call.departure < plan.first_period_end:
                            this_early_departure = subtract_times(roll_call.arrival, plan.first_period_end)
                            if plan.permitted_acceleration is not None and plan.permitted_acceleration > 0:
                                if this_early_departure < plan.permitted_acceleration:
                                    this_early_departure = 0

                        if roll_call.departure > plan.first_period_end:
                            this_late_departure = subtract_times(plan.first_period_end, roll_call.departure)
                            if this_late_arrival > 0:
                                if plan.floating_time is not None and plan.floating_time > 0:
                                    f = min(plan.floating_time, this_late_arrival)
                                    if this_late_departure > f:
                                        this_late_departure -= f
                                        this_late_arrival -= f
                                    else:
                                        this_late_arrival -= this_late_departure
                                        this_late_departure = 0

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



                elif plan.plan_type == WorkShiftPlan.FLOATING_PLAN_TYPE:
                    if total_minutes > plan.daily_duty_duration:
                        this_overtime = total_minutes - plan.daily_duty_duration
                        if plan.daily_overtime_limit is not None and plan.daily_overtime_limit > 0:
                            overtime[date_str] = min(this_overtime, plan.daily_overtime_limit)
                            if this_overtime > plan.daily_overtime_limit:
                                burned_out[date_str] = this_overtime - plan.daily_overtime_limit
                else:
                    return Response({"msg": "WorkShiftPlan PLAN_TYPE is not acceptable"}, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                if plan.plan_type == WorkShiftPlan.SIMPLE_PLAN_TYPE:
                    # first_duration = (plan.first_period_end.hour * 60 + plan.first_period_end.minute) - (plan.first_period_start.hour * 60 + plan.first_period_start.minute)
                    # first_duration = subtract_times(plan.first_period_start, plan.first_period_end)
                    # this_absent = first_duration
                    # if plan.second_period_start is not None and plan.second_period_end is not None:
                    #     this_absent += subtract_times(plan.second_period_start, plan.second_period_end)
                    absent[date_str] = calculate_daily_shift_duration(plan)
                elif plan.plan_type == WorkShiftPlan.FLOATING_PLAN_TYPE:
                    absent[date_str] = plan.daily_duty_duration
                else:
                    return Response({"msg": "WorkShiftPlan PLAN_TYPE is not acceptable"}, status=status.HTTP_406_NOT_ACCEPTABLE)

        result.append({
            "total_attend": "{}:{}".format(hours, minutes),
            "total_absent": sum(absent.values()),
            "total_overtime": sum(overtime.values()),
            "total_burned_out": sum(burned_out.values()),
            "total_mission": sum(mission.values()),
            "total_earned": sum(earned.values()),
            "total_sick": sum(sick.values()),
            "total_unpaid": sum(unpaid.values()),

            "days_attended": days_attended,
            "absent": absent,
            "attend": attend,
            "overtime": overtime,
            "burned_out": burned_out,
            "mission": mission,
            "earned": earned,
            "sick": sick,
            "unpaid": unpaid,
            "hours": hours, "minutes": minutes, })
    return Response(result, status=status.HTTP_200_OK)
