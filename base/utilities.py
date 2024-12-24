import random

from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.db.models import Q

def get_random_int_code(digits=4):
    a=pow(10,digits-1)
    b=pow(10,digits)
    return random.randint(a,b)