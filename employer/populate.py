import datetime
import random
from datetime import timedelta

from django.utils.timezone import now

from employer.models import RollCall


def populate_roll_call(employee_id):
    samples = []
    klas = RollCall
    for i in range(1, 11):
        hour = now().hour + random.randint(1, 8)
        minute = random.randint(1, 59)
        second = random.randint(1, 59)
        samples.append(klas(
            employee_id=employee_id,
            date=now() - timedelta(days=i),
            # arrival=datetime.time(hour,minute,second),
            departure=datetime.time(hour, minute, second),
        ))
    klas.objects.bulk_create(samples)
    # print(samples)
