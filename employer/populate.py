import datetime
import random
from datetime import timedelta

from django.utils.timezone import now

from employer.models import RollCall, WorkShiftPlan
from employer.serializers import WorkShiftPlanSerializer, WorkShiftPlanUpdateSerializer


def populate_roll_call(employee_id):
    samples = []
    klas = RollCall
    for i in range(1, 11):
        hour = 8 + random.randint(1, 4)
        minute = random.randint(1, 50)
        second = random.randint(1, 50)
        samples.append(klas(
            employee_id=employee_id,
            date=now() - timedelta(days=i),
            arrival=datetime.time(hour, minute, second),
            departure=datetime.time(hour + random.randint(1, 5), minute + random.randint(1, 5), second + random.randint(1, 5)),
        ))
    klas.objects.bulk_create(samples)
    # print(samples)


def populate_shift_plans(request,workshift_id=1):
    plans = []
    first_date = datetime.date(2025, 1, 1)
    for i in range(1, 364):
        this_date = first_date + timedelta(days=i)
        plans.append({
            "employer":request.user.id,
            "work_shift":workshift_id,
            "date":this_date,
            "plan_type":1,
            "daily_duty_duration":40,
            "floating_time":30,
            "daily_overtime_limit":10,
            "beginning_overtime":10,
            "middle_overtime":10,
            "ending_overtime":10,
            "permitted_delay":10,
            "permitted_acceleration":10,
            "pre_shift_floating":10,
            "permitted_traffic_start":"17:30:00",
            "permitted_traffic_end":"18:30:00",
            "is_night_shift":True,
            "reset_time":"04:30:00",
            "first_period_start":"17:30:00",
            "first_period_end":"18:30:00",
            "second_period_start":"17:30:00",
            "second_period_end":"18:30:00",
            "modifier_id":request.user.id,
        })
    ser=WorkShiftPlanUpdateSerializer(data=plans,many=True,context={'request':request})
    if ser.is_valid(raise_exception=True):
        ser.save()
    else:
        print(ser.errors)

