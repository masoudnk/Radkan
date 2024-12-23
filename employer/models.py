from django.core.validators import MinLengthValidator, int_list_validator
from django.db import models
from django_jalali.db import models as jmodels
from phonenumber_field.modelfields import PhoneNumberField

from base.models import get_file_path, City


class LegalEntityType(models.Model):
    name = models.CharField(max_length=250)


class Employer(models.Model):
    national_code = models.CharField(max_length=250)
    email = models.EmailField(null=True, blank=True, verbose_name='ایمیل')
    image = models.ImageField(upload_to=get_file_path, max_length=255, verbose_name='عکس پروفایل')
    mobile = PhoneNumberField(unique=True, verbose_name='شماره همراه')
    name = models.CharField(max_length=255, verbose_name='نام کاربری')
    password = models.CharField(max_length=255, verbose_name='رمز عبور')
    gender_choices = (
        (True, 'آقا'),
        (False, 'خانم'),
    )
    male_gender = models.BooleanField(null=True, blank=True, default=gender_choices[0][0], choices=gender_choices, verbose_name='جنسیت')
    personality_choices = (
        (1, 'حقیقی'),
        (2, 'حقوقی'),
    )
    personality = models.PositiveSmallIntegerField(default=personality_choices[0][0], choices=personality_choices, verbose_name='نوع کاربری')
    birth_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ تولد')
    phone = PhoneNumberField(verbose_name='تلفن')
    postal_code = models.CharField(max_length=10, validators=[int_list_validator(sep=''), MinLengthValidator(10), ], null=True, blank=True, )
    address = models.TextField(null=True, blank=True, verbose_name="آدرس")
    referrer = models.ForeignKey("self", on_delete=models.PROTECT)
    company_name = models.CharField(max_length=250)
    legal_entity_type = models.ForeignKey(LegalEntityType, on_delete=models.PROTECT, null=True, blank=True)
    company_registration_date = models.DateField(null=True, blank=True)
    company_registration_number = models.PositiveIntegerField(null=True, blank=True)
    branch_name = models.CharField(max_length=250)
    economical_code = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class AttendanceDeviceBrand(models.Model):
    name = models.CharField(max_length=250)


class AttendanceDevice(models.Model):
    status_choices = (
        (True, 'آنلاین'),
        (False, 'آفلاین'),
    )
    port = models.PositiveSmallIntegerField(default=4730)
    brand = models.ForeignKey(AttendanceDeviceBrand, on_delete=models.PROTECT)
    ip_address = models.GenericIPAddressField()
    status = models.BooleanField(null=True, blank=True, default=status_choices[0][0], choices=status_choices, verbose_name='وضعیت دستگاه')


class Workplace(models.Model):
    gender_choices = (
        (1, 'دایره'),
        (2, 'چند ضلعی'),
    )
    name = models.CharField(max_length=250)
    city = models.ForeignKey(City, on_delete=models.PROTECT)
    address = models.TextField(null=True, blank=True, )
    shape = models.PositiveSmallIntegerField(null=True, blank=True, default=gender_choices[0][0], choices=gender_choices, verbose_name='شکل هندسی محل کار')
    radius = models.PositiveSmallIntegerField(default=50, verbose_name="شعاع(متر)")

    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='عرض جغرافیایی')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='طول جغرافیایی')
    BSSID = models.CharField(max_length=250)

    def __str__(self):
        return self.name


class WorkPolicy(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class BasePolicy(models.Model):
    work_policy = models.OneToOneField(WorkPolicy, on_delete=models.PROTECT)
    maximum_hour_per_year = models.PositiveSmallIntegerField(help_text="minutes")
    maximum_minute_per_year = models.PositiveSmallIntegerField(help_text="minutes")
    maximum_hour_per_month = models.PositiveSmallIntegerField(help_text="minutes")
    maximum_minute_per_month = models.PositiveSmallIntegerField(help_text="minutes")

    class Meta:
        abstract = True


class ManualTrafficPolicy(models.Model):
    work_policy = models.OneToOneField(WorkPolicy, on_delete=models.PROTECT)
    maximum_per_year = models.PositiveSmallIntegerField(help_text="minutes")
    maximum_per_month = models.PositiveSmallIntegerField(help_text="minutes")
    acceptable_registration_days = models.PositiveSmallIntegerField()


class SecondPolicy(BasePolicy):
    maximum_daily_request_per_year = models.PositiveSmallIntegerField()
    maximum_daily_request_per_month = models.PositiveSmallIntegerField()

    class Meta:
        abstract = True


class OvertimePolicy(SecondPolicy):
    acceptable_registration_days = models.PositiveSmallIntegerField()


class LeavePolicy(SecondPolicy):
    maximum_hourly_request_per_year = models.PositiveSmallIntegerField()
    maximum_hourly_request_per_month = models.PositiveSmallIntegerField()
    acceptable_registration_type_choices = (
        (1, 'قبل'),
        (2, 'بعد'),
    )
    acceptable_daily_registration_type = models.PositiveSmallIntegerField(choices=acceptable_registration_type_choices, default=acceptable_registration_type_choices[0][0])
    acceptable_daily_registration_days = models.PositiveSmallIntegerField()
    acceptable_hourly_registration_type = models.PositiveSmallIntegerField(choices=acceptable_registration_type_choices, default=acceptable_registration_type_choices[0][0])
    acceptable_hourly_registration_days = models.PositiveSmallIntegerField()

    class Meta:
        abstract = True


class EarnedLeavePolicy(LeavePolicy):
    year = models.PositiveSmallIntegerField()
    maximum_earned_leave_for_next_year = models.PositiveSmallIntegerField(help_text="minutes")


class SickLeavePolicy(LeavePolicy):
    pass


class WorkMissionPolicy(LeavePolicy):
    pass


class Holiday(models.Model):
    name = models.CharField(max_length=250)
    date = models.DateField()

    def __str__(self):
        return self.name


#
# class SickLeavePolicy(models.Model):
#     work_policy = models.OneToOneField(WorkPolicy, on_delete=models.PROTECT)
#     year = models.PositiveSmallIntegerField()
#     maximum_sick_leave_per_year = models.PositiveSmallIntegerField(help_text="minutes")
#     maximum_sick_leave_per_month = models.PositiveSmallIntegerField(help_text="minutes")
#     # maximum_sick_leave_for_next_year = models.PositiveSmallIntegerField(help_text="minutes")
#     maximum_daily_sick_leave_request_per_year = models.PositiveSmallIntegerField()
#     maximum_hourly_sick_leave_request_per_year = models.PositiveSmallIntegerField()
#     maximum_daily_sick_leave_request_per_month = models.PositiveSmallIntegerField()
#     maximum_hourly_sick_leave_request_per_month = models.PositiveSmallIntegerField()
#     acceptable_registration_type_choices = (
#         (1, 'قبل'),
#         (2, 'بعد'),
#     )
#     acceptable_daily_registration_type=models.PositiveSmallIntegerField(choices=acceptable_registration_type_choices, default=acceptable_registration_type_choices[0][0])
#     acceptable_daily_sick_leave_registration_days = models.PositiveSmallIntegerField()
#     acceptable_hourly_registration_type=models.PositiveSmallIntegerField(choices=acceptable_registration_type_choices, default=acceptable_registration_type_choices[0][0])
#     acceptable_hourly_sick_leave_registration_days = models.PositiveSmallIntegerField()
#

class WorkShift(models.Model):
    name = models.CharField(max_length=250)
    date = jmodels.jDateField()
    floating_time = models.PositiveSmallIntegerField()
    daily_overtime_limit = models.PositiveSmallIntegerField()
    beginning_overtime = models.PositiveSmallIntegerField(null=True, blank=True)
    middle_overtime = models.PositiveSmallIntegerField(null=True, blank=True)
    ending_overtime = models.PositiveSmallIntegerField(null=True, blank=True)
    permitted_delay = models.PositiveSmallIntegerField(null=True, blank=True)
    permitted_acceleration = models.PositiveSmallIntegerField(null=True, blank=True)
    pre_shift_floating = models.PositiveSmallIntegerField(null=True, blank=True)
    permitted_traffic_start = models.TimeField(null=True, blank=True)
    permitted_traffic_end = models.TimeField(null=True, blank=True)
    first_period_start = models.TimeField(null=True, blank=True)
    first_period_end = models.TimeField(null=True, blank=True)
    second_period_start = models.TimeField(null=True, blank=True)
    second_period_end = models.TimeField(null=True, blank=True)
