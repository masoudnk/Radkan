import random

from django.db.models import ExpressionWrapper, Sum, DurationField, F


def get_random_int_code(digits=4):
    a = pow(10, digits - 1)
    b = pow(10, digits)
    return random.randint(a, b)


def time_to_minute(time_field):
    return time_field.hour * 60 + time_field.minute


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

