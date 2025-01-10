import random

from django.core.exceptions import ValidationError
from django.db.models import ExpressionWrapper, Sum, DurationField, F


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
    this_absent = first_duration
    if plan.second_period_start is not None and plan.second_period_end is not None:
        this_absent += subtract_times(plan.second_period_start, plan.second_period_end)
    return this_absent


def calculate_query_duration(q):
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
        raise ValidationError( msg)
    length = len(national_code)
    if length != 10:
        if 8 > length or length > 10:
            msg = "national-code must be 10 digits"
            raise ValidationError( msg)
        code = ((10 - length) * "0") + national_code
    else:
        code = national_code
    total = 0
    for i, c in enumerate(code[:-1]):
        total += int(c) * (10 - i)
    if total == 0:
        msg = "national-code is unacceptable"
        raise ValidationError( msg)
    controller = total % 11
    if controller < 2:
        if controller == int(national_code[-1]):
            return
        else:
            msg = "invalid controller"
            raise ValidationError( msg)
    elif controller == (11 - int(national_code[-1])):
        return
    else:
        msg = "national-code is unacceptable"
        raise ValidationError( msg)
