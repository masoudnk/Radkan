import datetime
import random
from datetime import timedelta

from django.utils.timezone import now

from employer.models import RollCall
from employer.serializers import WorkShiftPlanUpdateSerializer
from employer.utilities import DATE_FORMAT_STR


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


def populate_shift_plans(request, workshift_id=1):
    plans = []
    first_date = datetime.date(2025, 1, 1)
    for i in range(1, 364):
        this_date = first_date + timedelta(days=i)
        plans.append({
            # "id": 3635 + i,
            "employer": request.user.id,
            "work_shift": workshift_id,
            "date": this_date.strftime(DATE_FORMAT_STR),
            "plan_type": 1,
            "daily_duty_duration": random.randint(1, 60),
            "floating_time": random.randint(1, 50),
            "daily_overtime_limit": random.randint(1, 50),
            "beginning_overtime": random.randint(1, 50),
            "middle_overtime": random.randint(1, 50),
            "ending_overtime": random.randint(1, 50),
            "permitted_delay": random.randint(1, 50),
            "permitted_acceleration": random.randint(1, 50),
            "pre_shift_floating": random.randint(1, 50),
            "permitted_traffic_start": "6:30:00",
            "permitted_traffic_end": "21:30:00",
            "is_night_shift": True,
            "reset_time": "04:30:00",
            "first_period_start": "{:02d}:{:02d}:00".format(random.randint(8, 10), random.randint(0, 59)),
            "first_period_end": "{:02d}:{:02d}:00".format(random.randint(10, 12), random.randint(0, 59)),
            "second_period_start": "{:02d}:{:02d}:00".format(random.randint(16, 18), random.randint(0, 59)),
            "second_period_end": "{:02d}:{:02d}:00".format(random.randint(18, 20), random.randint(0, 59)),
            "modifier_id": request.user.id,
        })
    ser = WorkShiftPlanUpdateSerializer(data=plans, many=True, context={'request': request})
    if ser.is_valid(raise_exception=True):
        ser.save()
    else:
        print(ser.errors)
