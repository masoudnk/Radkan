import os
import uuid

from django.core.validators import MinLengthValidator, int_list_validator
from django.db import models
from django.utils import timezone
from django_jalali.db import models as jmodels
from phonenumber_field.modelfields import PhoneNumberField

from base.models import City
from base.utilities import get_random_int_code


class LegalEntityType(models.Model):
    name = models.CharField(max_length=250)


def get_employer_image_file_path(instance, filename, ):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4().hex, ext)
    return os.path.join('EmployerImage/' + uuid.uuid4().hex, filename)


from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin, _user_has_perm, _user_has_module_perms


# Create your models here.
class CustomUserManager(BaseUserManager):

    def create_user(self, username, password=None):
        if not username:
            raise ValueError('Users must have an username')
        user = self.model(
            username=username,
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username, password):
        user = self.create_user(
            username,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        # unique=True,
    )
    username = models.CharField(max_length=255, verbose_name='نام کاربری',unique=True)
    mobile = PhoneNumberField(
        # unique=True,
        verbose_name='شماره همراه')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # a admin user; non super-user
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField("date joined", default=timezone.now)
    objects = CustomUserManager()
    # notice the absence of a "Password field", that is built in.

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []


    def has_perm(self, perm, obj=None):
        if self.is_active and self.is_superuser:
            return True
        return _user_has_perm(self, perm, obj)


    def has_module_perms(self, app_label):
        if self.is_active and self.is_superuser:
            return True

        return _user_has_module_perms(self, app_label)



class ResetPasswordRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    code=models.PositiveSmallIntegerField(default=get_random_int_code)
    active = models.BooleanField(default=True)
    request_date= jmodels.jDateTimeField(auto_now_add=True)

class Employer(User):
    accepted_rules=models.BooleanField(default=False)
    national_code = models.CharField(max_length=250,null=True, blank=True)
    image = models.ImageField(upload_to=get_employer_image_file_path, max_length=255, verbose_name='عکس پروفایل',null=True, blank=True)
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
    phone = PhoneNumberField(verbose_name='تلفن',null=True, blank=True)
    postal_code = models.CharField(max_length=10, validators=[int_list_validator(sep=''), MinLengthValidator(10), ], null=True, blank=True, )
    address = models.TextField(null=True, blank=True, verbose_name="آدرس")
    referrer = models.ForeignKey("self", on_delete=models.PROTECT,null=True,blank=True)
    company_name = models.CharField(max_length=250,null=True, blank=True)
    legal_entity_type = models.ForeignKey(LegalEntityType, on_delete=models.PROTECT, null=True, blank=True)
    company_registration_date = models.DateField(null=True, blank=True)
    company_registration_number = models.PositiveIntegerField(null=True, blank=True)
    branch_name = models.CharField(max_length=250, null=True, blank=True)
    economical_code = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.username


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



class Employee(User):
    # gender_choices = (
    #     (True, 'آقا'),
    #     (False, 'خانم'),
    # )
    # male_gender = models.BooleanField(null=True, blank=True, default=gender_choices[0][0], choices=gender_choices, verbose_name='جنسیت')
    # birth_date = jmodels.jDateField(null=True, blank=True, verbose_name='تاریخ تولد')
    # image = models.ImageField(upload_to=get_file_path, max_length=255, verbose_name='عکس پروفایل')
    # mobile = PhoneNumberField(unique=True, verbose_name='شماره همراه')
    # email = models.EmailField(null=True, blank=True, verbose_name='ایمیل')
    first_name = models.CharField(max_length=255, verbose_name='نام')
    last_name = models.CharField(max_length=255, verbose_name='نام خانوادگی')
    # user_name = models.CharField(max_length=255, verbose_name='نام کاربری')
    # password = models.CharField(max_length=255, verbose_name='رمز عبور')
    national_code = models.CharField(max_length=250, null=True, blank=True, verbose_name="کد ملی")
    personnel_code = models.CharField(max_length=250)
    workplace = models.ForeignKey(Workplace, on_delete=models.PROTECT)
    work_policy = models.ForeignKey(WorkPolicy, on_delete=models.PROTECT)
    work_shift = models.ForeignKey(WorkShift, on_delete=models.PROTECT)
    shift_start_date = models.DateField()
    shift_end_date = models.DateField()
    use_gps = models.BooleanField(default=False)
    use_wifi = models.BooleanField(default=False)
    device_choices = (
        (1, 'اپلیکیشن وب (pwa)'),
        (2, 'اپلیکیشن اندروید'),
        (3, 'هر دو نوع دستگاه (وب و اندروید)'),
        (4, 'دستگاه حضور و غیاب'),
    )
    limit_devices = models.PositiveSmallIntegerField(choices=device_choices, default=device_choices[0][0])
    interception = models.BooleanField(default=False)

    def __str__(self):
        return self.first_name + " " + self.last_name


class EmployeeRequestCategory(models.Model):
    name = models.CharField(max_length=250)


class EmployeeRequest(models.Model):
    category = models.ForeignKey(EmployeeRequestCategory, on_delete=models.PROTECT)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    registration_date = models.DateField(auto_now_add=True)
    action_choices = (
        (1, "در دست بررسی"),
        (2, "تایید شده"),
        (3, "تایید شده"),
    )

class Project(models.Model):
    name = models.CharField(max_length=250)
    status = models.BooleanField()
    employee = models.ManyToManyField(Employee)


class WorkCategory(models.Model):
    name = models.CharField(max_length=250)
    parent = models.ForeignKey("self", on_delete=models.PROTECT,null=True, blank=True)
    employee = models.ManyToManyField(Employee)


class RadkanMessage(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField()
    work_category = models.ForeignKey(WorkCategory, on_delete=models.PROTECT)
    employee = models.ManyToManyField(Employee)
