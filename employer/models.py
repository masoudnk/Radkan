import os
import uuid

from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin, _user_has_perm, _user_has_module_perms
from django.contrib.auth.models import Permission
from django.core.validators import MinLengthValidator, int_list_validator
from django.db import models
from django.utils import timezone
from django_jalali.db import models as jmodels
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from phonenumber_field.modelfields import PhoneNumberField

from employer.utilities import get_random_int_code


class LegalEntityType(models.Model):
    name = models.CharField(max_length=250)


def get_ticket_attachment_file_path(instance, filename, ):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4().hex, ext)
    return os.path.join('TicketAttachments/' + uuid.uuid4().hex, filename)


def get_employer_image_file_path(instance, filename, ):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4().hex, ext)
    return os.path.join('EmployerImage/' + uuid.uuid4().hex, filename)


class CustomUserManager(BaseUserManager):

    def create_user(self, mobile, password=None):
        if not mobile:
            raise ValueError('Users must have an username')
        user = self.model(
            mobile=mobile,
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, mobile, password):
        user = self.create_user(
            mobile,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    # email = models.EmailField(
    #     verbose_name='email address',
    #     max_length=255,
    #     # unique=True,
    # )
    username = models.CharField(max_length=255, verbose_name='نام کاربری', )
    mobile = PhoneNumberField(
        unique=True,
        verbose_name='شماره همراه')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    registration_date = jmodels.jDateTimeField(default=timezone.now)
    objects = CustomUserManager()
    # notice the absence of a "Password field", that is built in.

    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = []

    def __str__(self):
        return str(self.mobile)

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
    code = models.PositiveSmallIntegerField(default=get_random_int_code)
    active = models.BooleanField(default=True)
    request_date = jmodels.jDateTimeField(auto_now_add=True)


class Manager(User):
    employer_id = models.PositiveIntegerField()


class Employer(User):
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True, )
    accepted_rules = models.BooleanField(default=False)
    national_code = models.CharField(max_length=250, null=True, blank=True)
    # image = models.ImageField(upload_to=get_employer_image_file_path, max_length=255, verbose_name='عکس پروفایل', null=True, blank=True)
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
    phone = PhoneNumberField(verbose_name='تلفن', null=True, blank=True)
    postal_code = models.CharField(max_length=10, validators=[int_list_validator(sep=''), MinLengthValidator(10), ], null=True, blank=True, )
    address = models.TextField(null=True, blank=True, verbose_name="آدرس")
    referrer = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True)
    company_name = models.CharField(max_length=250, null=True, blank=True)
    legal_entity_type = models.ForeignKey(LegalEntityType, on_delete=models.PROTECT, null=True, blank=True)
    company_registration_date = jmodels.jDateField(null=True, blank=True)
    company_registration_number = models.PositiveIntegerField(null=True, blank=True)
    company_national_id = models.PositiveIntegerField(null=True, blank=True)
    branch_name = models.CharField(max_length=250, null=True, blank=True)
    economical_code = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.username
    # class Meta:
    #     permissions = [("","")]


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
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    # gender_choices = (
    #     (1, 'دایره'),
    #     (2, 'چند ضلعی'),
    # )
    name = models.CharField(max_length=250)
    province = models.ForeignKey("Province", on_delete=models.PROTECT)
    city = models.ForeignKey("City", on_delete=models.PROTECT)
    address = models.TextField(null=True, blank=True, )
    # shape = models.PositiveSmallIntegerField(null=True, blank=True, default=gender_choices[0][0], choices=gender_choices, verbose_name='شکل هندسی محل کار')
    radius = models.PositiveSmallIntegerField(default=50, verbose_name="شعاع(متر)")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='عرض جغرافیایی')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='طول جغرافیایی')
    BSSID = models.CharField(max_length=250)

    def __str__(self):
        return self.name


class WorkPolicy(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
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
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    work_policy = models.OneToOneField(WorkPolicy, on_delete=models.PROTECT)
    maximum_per_year = models.PositiveSmallIntegerField()
    maximum_per_month = models.PositiveSmallIntegerField()
    acceptable_registration_days = models.PositiveSmallIntegerField()


class SecondPolicy(BasePolicy):
    maximum_daily_request_per_year = models.PositiveSmallIntegerField()
    maximum_daily_request_per_month = models.PositiveSmallIntegerField()

    class Meta:
        abstract = True


class OvertimePolicy(SecondPolicy):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    acceptable_registration_days = models.PositiveSmallIntegerField()


class LeavePolicy(SecondPolicy):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    maximum_hourly_request_per_year = models.PositiveSmallIntegerField()
    maximum_hourly_request_per_month = models.PositiveSmallIntegerField()
    acceptable_registration_type_choices = (
        (1, 'قبل'),
        (2, 'بعد'),
    )
    acceptable_daily_registration_type = models.PositiveSmallIntegerField(choices=acceptable_registration_type_choices, )
    # acceptable_daily_registration_type = models.PositiveSmallIntegerField(choices=acceptable_registration_type_choices, default=acceptable_registration_type_choices[0][0])
    acceptable_daily_registration_days = models.PositiveSmallIntegerField()
    acceptable_hourly_registration_type = models.PositiveSmallIntegerField(choices=acceptable_registration_type_choices, )
    # acceptable_hourly_registration_type = models.PositiveSmallIntegerField(choices=acceptable_registration_type_choices, default=acceptable_registration_type_choices[0][0])
    acceptable_hourly_registration_days = models.PositiveSmallIntegerField()

    class Meta:
        abstract = True


class EarnedLeavePolicy(LeavePolicy):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    year = models.PositiveSmallIntegerField()
    maximum_earned_leave_for_next_year_hour = models.PositiveSmallIntegerField(help_text="hour")
    maximum_earned_leave_for_next_year_minutes = models.PositiveSmallIntegerField(help_text="minutes")

    class Meta:
        permissions = [("update", "update EarnedLeavePolicy")]


class SickLeavePolicy(LeavePolicy):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)


class WorkMissionPolicy(LeavePolicy):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)


class Holiday(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    date = jmodels.jDateField()

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
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    maximum_shiftless_day_overtime = models.PositiveSmallIntegerField(help_text="minutes")
    observance_of_public_holidays = models.BooleanField(default=False)
    year = models.PositiveSmallIntegerField()


class WorkShiftPlan(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    work_shift = models.ForeignKey(WorkShift, on_delete=models.CASCADE)
    date = jmodels.jDateField()
    plan_type_choices = (
        (1, "ساده"),
        (2, "شناور"),
    )
    plan_type = models.PositiveSmallIntegerField(choices=plan_type_choices, default=plan_type_choices[0][0])
    daily_duty_duration = models.PositiveSmallIntegerField(help_text="minutes", null=True, blank=True)
    floating_time = models.PositiveSmallIntegerField(help_text="minutes", null=True, blank=True)
    daily_overtime_limit = models.PositiveSmallIntegerField()
    beginning_overtime = models.PositiveSmallIntegerField(null=True, blank=True)
    middle_overtime = models.PositiveSmallIntegerField(null=True, blank=True)
    ending_overtime = models.PositiveSmallIntegerField(null=True, blank=True)
    permitted_delay = models.PositiveSmallIntegerField(null=True, blank=True)
    permitted_acceleration = models.PositiveSmallIntegerField(null=True, blank=True)
    pre_shift_floating = models.PositiveSmallIntegerField(null=True, blank=True)
    permitted_traffic_start = models.TimeField(null=True, blank=True)
    permitted_traffic_end = models.TimeField(null=True, blank=True)
    is_night_shift = models.BooleanField(default=False)
    reset_time = models.TimeField(null=True, blank=True)
    first_period_start = models.TimeField(null=True, blank=True)
    first_period_end = models.TimeField(null=True, blank=True)
    second_period_start = models.TimeField(null=True, blank=True)
    second_period_end = models.TimeField(null=True, blank=True)
    # fixme this uniqueness will create "AttributeError: 'list' object has no attribute 'pk'" error on serializer
    # class Meta:
    #     unique_together=("work_shift", "date")


class Employee(User):
    active = models.BooleanField(default=True)
    employer_id = models.PositiveIntegerField(editable=False)
    first_name = models.CharField(max_length=255, verbose_name='نام')
    last_name = models.CharField(max_length=255, verbose_name='نام خانوادگی')
    national_code = models.CharField(max_length=250, null=True, blank=True, verbose_name="کد ملی")
    personnel_code = models.CharField(max_length=250)
    workplace = models.ForeignKey(Workplace, on_delete=models.PROTECT)
    work_policy = models.ForeignKey(WorkPolicy, on_delete=models.PROTECT)
    work_shift = models.ForeignKey(WorkShift, on_delete=models.PROTECT)
    shift_start_date = jmodels.jDateField()
    shift_end_date = jmodels.jDateField()

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def __str__(self):
        return self.get_full_name()


class EmployeeRequestCategory(models.Model):
    name = models.CharField(max_length=250)


class EmployeeRequest(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT, null=True, blank=True)
    # todo change category to CHOICE
    category = models.ForeignKey(EmployeeRequestCategory, on_delete=models.PROTECT)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    # start_date = jmodels.jDateField()
    end_date = jmodels.jDateField(null=True,blank=True)
    registration_date = jmodels.jDateField(auto_now_add=True)
    action_choices = (
        (1, "در دست بررسی"),
        (2, "تایید شده"),
        (3, "تایید شده"),
    )
    action = models.PositiveSmallIntegerField(choices=action_choices, default=action_choices[0][0])
    description = models.TextField(null=True, blank=True)
    workplace = models.ForeignKey(Workplace, on_delete=models.PROTECT, null=True, blank=True)
    date = jmodels.jDateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    traffic_choices = (
        (1, "ورود"),
        (2, "خروج"),
    )
    # from_time = models.TimeField(null=True, blank=True)
    to_time = models.TimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='عرض جغرافیایی', null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='طول جغرافیایی', null=True, blank=True)
    attachment = models.FileField(upload_to=get_ticket_attachment_file_path, max_length=200, null=True, blank=True)
    project = models.ForeignKey("Project", on_delete=models.PROTECT, null=True, blank=True)
    other_employee = models.ForeignKey("Employee", on_delete=models.PROTECT, null=True, blank=True)


class Project(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    status = models.BooleanField()
    employee = models.ManyToManyField(Employee)


class WorkCategory(MPTTModel):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    parent = TreeForeignKey("self", related_name='children', on_delete=models.PROTECT, null=True, blank=True)
    employee = models.ManyToManyField(Employee)

    class MPTTMeta:
        order_insertion_by = ['name']


class RadkanMessage(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    title = models.CharField(max_length=250)
    description = models.TextField()
    work_category = models.ForeignKey(WorkCategory, on_delete=models.PROTECT)
    employee = models.ManyToManyField(Employee)


class Province(models.Model):
    name = models.CharField(max_length=255, verbose_name='استان')

    class Meta:
        verbose_name = 'استان'
        verbose_name_plural = 'استان ها'

    def __str__(self):
        return self.name


class City(models.Model):
    parent = models.ForeignKey(Province, on_delete=models.CASCADE, verbose_name='استان')
    name = models.CharField(max_length=255, verbose_name='نام')

    # latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='عرض جغرافیایی')
    # longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='طول جغرافیایی')

    class Meta:
        verbose_name = 'شهر'
        verbose_name_plural = 'شهر ها'

    def __str__(self):
        return self.name


class TicketSection(models.Model):
    name = models.CharField(max_length=250)


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    title = models.CharField(max_length=250)
    # section_choices = (
    #     ("SUPPORT", "پشتیبانی"),
    #     ("SALE", "فروش"),
    #     ("ADMINISTRATIVE", "اداری و مالی")
    # )
    # section = models.CharField(max_length=250)
    section = models.ForeignKey(TicketSection, on_delete=models.PROTECT)
    description = models.TextField()

    attachment = models.FileField(upload_to=get_ticket_attachment_file_path, max_length=200, null=True, blank=True)


class RollCall(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    date = jmodels.jDateField()
    arrival = models.TimeField(auto_now_add=True)
    departure = models.TimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='عرض جغرافیایی', null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='طول جغرافیایی', null=True, blank=True)
