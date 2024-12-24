import django.contrib.auth.password_validation as validators
from django.contrib.auth.hashers import make_password
from django.core import exceptions
from rest_framework import serializers

from employer.models import User, Employer

