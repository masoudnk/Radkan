import random
import re

import jdatetime
import pandas as pd
from django.core.exceptions import ValidationError
from django.db.models import ExpressionWrapper, Sum, DurationField, F, Q
from django.http import HttpResponse

from employer.models import WorkShiftPlan

POST_METHOD_STR = "POST"
GET_METHOD_STR = "GET"
PUT_METHOD_STR = "PUT"
DELETE_METHOD_STR = "DELETE"
DATE_FORMAT_STR = "%Y-%m-%d"
TIME_FORMAT_STR = "%H:%M"
DATE_TIME_FORMAT_STR = "%Y-%m-%d %H:%M"

ADD_PERMISSION_STR = "add"
CHANGE_PERMISSION_STR = "change"
DELETE_PERMISSION_STR = "delete"
VIEW_PERMISSION_STR = "view"

REPORT_PERMISSION_STR = "report"
DASHBOARD_PERMISSION_STR = "dashboard"


def get_random_int_code(digits=4):
    a = pow(10, digits - 1)
    b = pow(10, digits)
    return random.randint(a, b)


def time_to_minute(time_field):
    return time_field.hour * 60 + time_field.minute


def total_minute_to_hour_and_minutes(total_minute=0):
    hours = total_minute // 60
    minutes = total_minute % 60
    return "{}:{}".format(hours, minutes)


def subtract_times(start, end):
    return time_to_minute(end) - time_to_minute(start)


def calculate_daily_shift_duration(plan):
    first_duration = subtract_times(plan.first_period_start, plan.first_period_end)
    this_duration = first_duration
    if plan.second_period_start is not None and plan.second_period_end is not None:
        this_duration += subtract_times(plan.second_period_start, plan.second_period_end)
    return this_duration


def str_to_time(string):
    return jdatetime.datetime.strptime(string, TIME_FORMAT_STR).time()


def calculate_daily_request_duration(employee_requests, plans):
    total_duration = 0
    for emp_req in employee_requests:
        this_plans = plans.filter(Q(date__gte=emp_req.date) | Q(date__lte=emp_req.to_date))
        for plan in this_plans:
            total_duration += calculate_daily_shift_duration(plan)
    return total_duration


def calculate_hourly_request_duration(employee_requests):
    total_duration = 0
    for employee_request in employee_requests:
        total_duration += subtract_times(employee_request.time, employee_request.to_time)
    return total_duration


def calculate_roll_call_query_duration(q):
    q = q.annotate(duration=ExpressionWrapper(
        F('departure') - F('arrival'), output_field=DurationField()))
    total_time = q.aggregate(total_time=Sum('duration')).get('total_time')
    if total_time is not None:
        days = total_time.days * 24
        seconds = total_time.seconds
        total_minutes = seconds // 60
        hours = total_minutes // 60 + days
        minutes = total_minutes % 60
    else:
        minutes = total_minutes = hours = 0

    return hours, minutes, total_minutes


def national_code_validation(national_code: str):
    if national_code is None:
        return
    msg = ""
    if not national_code.isdecimal():
        msg = "national-code must be a decimal number"
        raise ValidationError(msg)
    length = len(national_code)
    if length != 10:
        if 8 > length or length > 10:
            msg = "national-code must be 10 digits"
            raise ValidationError(msg)
        code = ((10 - length) * "0") + national_code
    else:
        code = national_code
    total = 0
    for i, c in enumerate(code[:-1]):
        total += int(c) * (10 - i)
    if total == 0:
        msg = "national-code is unacceptable"
        raise ValidationError(msg)
    controller = total % 11
    if controller < 2:
        if controller == int(national_code[-1]):
            return
        else:
            msg = "invalid controller"
            raise ValidationError(msg)
    elif controller == (11 - int(national_code[-1])):
        return
    else:
        msg = "national-code is unacceptable"
        raise ValidationError(msg)


def send_response_file(data, file_name, file_format='excel'):
    df = pd.DataFrame(data)
    print(file_format)
    if file_format == 'excel':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename={}.xlsx'.format(file_name)
        df.to_excel(response, index=False, engine='openpyxl')
    elif file_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(file_name)
        df.to_csv(response, index=False)
    elif file_format == 'json':
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename={}.json'.format(file_name)
        response.write(df.to_json(orient='records'))
    else:
        response = HttpResponse("Unsupported format", status=400)

    return response


def mobile_validator(phone_number: str):
    phone_number = phone_number.replace("+", "00")
    if not phone_number.isdecimal():
        raise ValidationError("phone number must be a decimal number")
    if len(phone_number) < 10:
        raise ValidationError("phone number must be at least 10 digits")
    pattern = "^(?:(?:(?:\\+?|00)(98))|(0))?((?:90|91|92|93|99)[0-9]{8})$"
    if not re.match(pattern, phone_number):
        raise ValidationError("شماره موبایل نادرست است.")


def positive_only(func):
    def wrapper(*args, ):
        print("Before calling the function.")
        print(args)
        for i in args:
            if i < 0:
                print(i)
                raise ValidationError("i is negative")
        func(*args, )
        print("After calling the function.")

    return wrapper


class DailyStatus:
    middle_overtime = attend = overtime = absent = 0
    first_period_early_arrival = first_period_late_arrival = first_period_early_departure = first_period_late_departure = 0
    second_period_early_arrival = second_period_late_arrival = second_period_early_departure = second_period_late_departure = 0
    burned_out = {}

    def __init__(self, plan: WorkShiftPlan):
        self.plan: WorkShiftPlan = plan

    def get_date(self):
        return self.plan.date.strftime(DATE_FORMAT_STR)

    @positive_only
    def add_attend(self, attended):
        self.attend += attended

    @positive_only
    def add_absent(self, absented):
        self.absent += absented

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
