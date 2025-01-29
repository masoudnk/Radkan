import os
import uuid

from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin, _user_has_perm, _user_has_module_perms
from django.contrib.auth.models import Permission
from django.core.validators import MinLengthValidator, int_list_validator, MaxValueValidator
from django.db import models
from django_jalali.db import models as jmodels
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from phonenumber_field.modelfields import PhoneNumberField

from employer.utilities import get_random_int_code, national_code_validation, mobile_validator


class LegalEntityType(models.Model):
    name = models.CharField(max_length=250)


def get_file_path(instance, filename, ):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4().hex, ext)
    subfolder = uuid.uuid4().hex
    if isinstance(instance, Ticket):
        main_folder = 'TicketAttachments/'
    elif isinstance(instance, Employer):
        main_folder = 'EmployerImage/'
    elif isinstance(instance, Employee):
        main_folder = 'EmployeeImage/'
    elif isinstance(instance, EmployeeRequest):
        main_folder = 'SickLeaveRequestFiles/'
    else:
        raise Exception("unhandled model type used get_file_path() method")
    return os.path.join(main_folder + subfolder, filename)


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
    # fixme password wont hash if inserted from simple-admins
    # email = models.EmailField(
    #     verbose_name='email address',
    #     max_length=255,
    #     # unique=True,
    # )
    username = models.CharField(max_length=255, verbose_name='نام کاربری', )
    mobile = PhoneNumberField(
        unique=True,
        verbose_name='شماره همراه',
        validators=[mobile_validator])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    registration_date = jmodels.jDateTimeField(auto_now_add=True)
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
    expiration_date = jmodels.jDateTimeField()


class Employer(User):
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True, )
    accepted_rules = models.BooleanField(default=False)
    national_code = models.CharField(max_length=250, null=True, blank=True, validators=[national_code_validation])
    # image = models.ImageField(upload_to=get_employer_image_file_path, max_length=255, verbose_name='عکس پروفایل', null=True, blank=True)
    GENDER_CHOICES = {
        True: 'آقا',
        False: 'خانم',
    }
    is_male = models.BooleanField(default=True, choices=GENDER_CHOICES, verbose_name='جنسیت')
    PERSONALITY_PERSONAL = 1
    PERSONALITY_LEGAL = 2
    PERSONALITY_CHOICES = {
        PERSONALITY_PERSONAL: 'حقیقی',
        PERSONALITY_LEGAL: 'حقوقی',
    }
    personality = models.PositiveSmallIntegerField(default=PERSONALITY_PERSONAL, choices=PERSONALITY_CHOICES, verbose_name='نوع کاربری')
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
    email_login_successful = models.BooleanField(default=False)
    email_login_failed = models.BooleanField(default=True)
    email_change_password = models.BooleanField(default=True)
    email_employee_login = models.BooleanField(default=False)
    email_employee_logout = models.BooleanField(default=False)
    email_employee_request_registered = models.BooleanField(default=False)

    def __str__(self):
        return self.username
    # class Meta:
    #     permissions = [("","")]


class MelliSMSInfo(models.Model):
    employer = models.OneToOneField(Employer, on_delete=models.CASCADE)
    melli_sms_username = models.CharField(max_length=250)
    melli_sms_password = models.CharField(max_length=250)
    melli_sms_phone_number = models.CharField(max_length=250)
    sms_email_register_employee_request = models.BooleanField(default=False)
    sms_login_successful = models.BooleanField(default=False)
    sms_login_failed = models.BooleanField(default=False)
    sms_change_password = models.BooleanField(default=False)
    sms_employee_login = models.BooleanField(default=True)
    sms_employee_logout = models.BooleanField(default=True)
    sms_register_employee_request = models.BooleanField(default=True)


# class AttendanceDeviceBrand(models.Model):
#     name = models.CharField(max_length=250)


# class AttendanceDevice(models.Model):
#     STATUS_CHOICES = {
#         True: 'آنلاین',
#         False: 'آفلاین',
#     }
#     port = models.PositiveSmallIntegerField(default=4730)
#     brand = models.ForeignKey(AttendanceDeviceBrand, on_delete=models.PROTECT)
#     ip_address = models.GenericIPAddressField()
#     is_online = models.BooleanField(null=True, blank=True, default=True, choices=STATUS_CHOICES, verbose_name='وضعیت دستگاه')


class Workplace(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    city = models.CharField(max_length=250)
    address = models.TextField(null=True, blank=True, )
    radius = models.PositiveSmallIntegerField(default=50, verbose_name="شعاع(متر)")
    latitude = models.DecimalField(max_digits=17, decimal_places=14, verbose_name='عرض جغرافیایی')
    longitude = models.DecimalField(max_digits=17, decimal_places=14, verbose_name='طول جغرافیایی')


class RTSP(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    workplace = models.ForeignKey(Workplace, on_delete=models.PROTECT)
    rtsp_link = models.TextField()
    # rtsp_user_name  = models.CharField(max_length=250)
    # rtsp_password = models.CharField(max_length=250)
    Login = 1
    Logout = 2
    TRAFFIC_CHOICES = {
        Login: "ورود",
        Logout: "خروج",
    }
    traffic_type = models.PositiveSmallIntegerField(choices=TRAFFIC_CHOICES)


class WorkPolicy(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class BasePolicy(models.Model):
    work_policy = models.OneToOneField(WorkPolicy, on_delete=models.CASCADE)
    maximum_hour_per_year = models.PositiveSmallIntegerField(help_text="minutes")
    maximum_minute_per_year = models.PositiveSmallIntegerField(help_text="minutes", validators=[MaxValueValidator(59)])
    maximum_hour_per_month = models.PositiveSmallIntegerField(help_text="minutes")
    maximum_minute_per_month = models.PositiveSmallIntegerField(help_text="minutes", validators=[MaxValueValidator(59)])

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
    BEFORE = 1
    AFTER = 2
    ACCEPTABLE_REGISTRATION_TYPE_CHOICES = {
        BEFORE: 'قبل',
        AFTER: 'بعد',
    }
    acceptable_daily_registration_type = models.PositiveSmallIntegerField(choices=ACCEPTABLE_REGISTRATION_TYPE_CHOICES, )
    acceptable_daily_registration_days = models.PositiveSmallIntegerField()
    acceptable_hourly_registration_type = models.PositiveSmallIntegerField(choices=ACCEPTABLE_REGISTRATION_TYPE_CHOICES, )
    acceptable_hourly_registration_days = models.PositiveSmallIntegerField()

    class Meta:
        abstract = True


class EarnedLeavePolicy(LeavePolicy):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    year = models.PositiveSmallIntegerField()
    maximum_earned_leave_for_next_year_hour = models.PositiveSmallIntegerField(help_text="hour")
    maximum_earned_leave_for_next_year_minutes = models.PositiveSmallIntegerField(help_text="minutes", validators=[MaxValueValidator(59)])
    bypass_annual_limit = models.BooleanField(default=True)
    bypass_monthly_limit = models.BooleanField(default=True)

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

    class Meta:
        unique_together = (("employer", "date"),)


class WorkShift(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    maximum_shiftless_day_overtime = models.PositiveSmallIntegerField(help_text="minutes")
    observance_of_public_holidays = models.BooleanField(default=False)
    year = models.PositiveSmallIntegerField()

    class Meta:
        permissions = (
            ("view_report", "Can view report"),)


class WorkShiftPlan(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    work_shift = models.ForeignKey(WorkShift, on_delete=models.CASCADE)
    date = jmodels.jDateField()
    SIMPLE_PLAN_TYPE = 1
    FLOATING_PLAN_TYPE = 2
    PLAN_TYPE_CHOICES = {
        SIMPLE_PLAN_TYPE: "ساده",
        FLOATING_PLAN_TYPE: "شناور",
    }
    plan_type = models.PositiveSmallIntegerField(choices=PLAN_TYPE_CHOICES, default=SIMPLE_PLAN_TYPE)
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
    # optional field
    modifier = models.ForeignKey(User, on_delete=models.PROTECT, related_name="modifier")
    # fixme this uniqueness will create "AttributeError: 'list' object has no attribute 'pk'" error on serializer
    # class Meta:
    #     unique_together=("work_shift", "date")


class Employee(User):
    employer_id = models.PositiveIntegerField()
    first_name = models.CharField(max_length=255, verbose_name='نام')
    last_name = models.CharField(max_length=255, verbose_name='نام خانوادگی')
    national_code = models.CharField(max_length=250, null=True, blank=True, verbose_name="کد ملی", validators=[national_code_validation])
    personnel_code = models.CharField(max_length=250)
    workplace = models.ManyToManyField(Workplace)
    work_policy = models.ForeignKey(WorkPolicy, on_delete=models.PROTECT,null=True, blank=True)
    work_shift = models.ForeignKey(WorkShift, on_delete=models.PROTECT)
    shift_start_date = jmodels.jDateField()
    shift_end_date = jmodels.jDateField(null=True, blank=True)
    front_image = models.ImageField(upload_to=get_file_path, max_length=100, null=True, blank=True)
    up_image = models.ImageField(upload_to=get_file_path, max_length=100, null=True, blank=True)
    down_image = models.ImageField(upload_to=get_file_path, max_length=100, null=True, blank=True)
    left_image = models.ImageField(upload_to=get_file_path, max_length=100, null=True, blank=True)
    right_image = models.ImageField(upload_to=get_file_path, max_length=100, null=True, blank=True)
    front_second_image = models.ImageField(upload_to=get_file_path, max_length=100, null=True, blank=True)

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def __str__(self):
        return self.get_full_name()


# class EmployeeRequestCategory(models.Model):
#     name = models.CharField(max_length=250)


class EmployeeRequest(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT, null=True, blank=True)
    CATEGORY_MANUAL_TRAFFIC = 1
    CATEGORY_HOURLY_EARNED_LEAVE = 2
    CATEGORY_DAILY_EARNED_LEAVE = 3
    CATEGORY_HOURLY_MISSION = 4
    CATEGORY_DAILY_MISSION = 5
    CATEGORY_OVERTIME = 6
    CATEGORY_HOURLY_SICK_LEAVE = 7
    CATEGORY_DAILY_SICK_LEAVE = 8
    CATEGORY_HOURLY_UNPAID_LEAVE = 9
    CATEGORY_DAILY_UNPAID_LEAVE = 10
    CATEGORY_PROJECT_MANUAL_TRAFFIC = 11
    CATEGORY_SHIFT_ROTATION = 12

    CATEGORY_CHOICES = {
        CATEGORY_MANUAL_TRAFFIC: "تردد دستی",
        CATEGORY_HOURLY_EARNED_LEAVE: "مرخصی استحقاقی ساعتی",
        CATEGORY_DAILY_EARNED_LEAVE: "مرخصی استحقاقی روزانه",
        CATEGORY_HOURLY_MISSION: "ماموریت ساعتی",
        CATEGORY_DAILY_MISSION: "ماموریت روزانه",
        CATEGORY_OVERTIME: "اضافه کار",
        CATEGORY_HOURLY_SICK_LEAVE: "استعلاجی ساعتی",
        CATEGORY_DAILY_SICK_LEAVE: "استعلاجی روزانه",
        CATEGORY_HOURLY_UNPAID_LEAVE: "مرخصی بی حقوق ساعتی",
        CATEGORY_DAILY_UNPAID_LEAVE: "مرخصی بی حقوق روزانه",
        CATEGORY_PROJECT_MANUAL_TRAFFIC: "تردد دستی پروژه",
        CATEGORY_SHIFT_ROTATION: "جابجایی شیفت",
    }
    category = models.PositiveSmallIntegerField(choices=CATEGORY_CHOICES, )
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    # start_date = jmodels.jDateField()
    end_date = jmodels.jDateField(null=True, blank=True)
    registration_date = jmodels.jDateField(auto_now_add=True)

    STATUS_UNDER_REVIEW = 1
    STATUS_APPROVED = 2
    STATUS_REJECTED = 3
    STATUS_CHOICES = {
        STATUS_UNDER_REVIEW: "در دست بررسی",
        STATUS_APPROVED: "تایید شده",
        STATUS_REJECTED: "رد شده",
    }
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=STATUS_UNDER_REVIEW)
    description = models.TextField(null=True, blank=True)
    workplace = models.ForeignKey(Workplace, on_delete=models.PROTECT, null=True, blank=True)
    date = jmodels.jDateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    Login = 1
    Logout = 2
    TRAFFIC_CHOICES = {
        Login: "ورود",
        Logout: "خروج",
    }
    # from_time = models.TimeField(null=True, blank=True)
    manual_traffic_type = models.PositiveSmallIntegerField(choices=TRAFFIC_CHOICES, null=True, blank=True)
    to_time = models.TimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=17, decimal_places=14, verbose_name='عرض جغرافیایی', null=True, blank=True)
    longitude = models.DecimalField(max_digits=17, decimal_places=14, verbose_name='طول جغرافیایی', null=True, blank=True)
    attachment = models.FileField(upload_to=get_file_path, max_length=200, null=True, blank=True)
    project = models.ForeignKey("Project", on_delete=models.PROTECT, null=True, blank=True)
    other_employee = models.ForeignKey("Employee", related_name="other_employee", on_delete=models.PROTECT, null=True, blank=True)



class Project(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    status = models.BooleanField()
    employees = models.ManyToManyField(Employee)


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
    employees = models.ManyToManyField(Employee)
    date = jmodels.jDateField(auto_now_add=True)


class RadkanMessageViewInfo(models.Model):
    radkan_message = models.ForeignKey(RadkanMessage, on_delete=models.CASCADE)
    date_time = jmodels.jDateTimeField(auto_now_add=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("radkan_message", "employee")


#
# class Province(models.Model):
#     name = models.CharField(max_length=255, verbose_name='استان')
#
#     class Meta:
#         verbose_name = 'استان'
#         verbose_name_plural = 'استان ها'
#
#     def __str__(self):
#         return self.name
#
#
# class City(models.Model):
#     parent = models.ForeignKey(Province, on_delete=models.CASCADE, verbose_name='استان')
#     name = models.CharField(max_length=255, verbose_name='نام')
#
#     # latitude = models.DecimalField(max_digits=17, decimal_places=14, verbose_name='عرض جغرافیایی')
#     # longitude = models.DecimalField(max_digits=17, decimal_places=14, verbose_name='طول جغرافیایی')
#
#     class Meta:
#         verbose_name = 'شهر'
#         verbose_name_plural = 'شهر ها'
#
#     def __str__(self):
#         return self.name
#

class TicketSection(models.Model):
    name = models.CharField(max_length=250)


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    title = models.CharField(max_length=250)
    section = models.ForeignKey(TicketSection, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    date_time = jmodels.jDateTimeField(auto_now_add=True)
    description = models.TextField()
    attachment = models.FileField(upload_to=get_file_path, max_length=200, null=True, blank=True)


class TicketConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT)
    date_time = jmodels.jDateTimeField(auto_now_add=True)
    description = models.TextField()
    attachment = models.FileField(upload_to=get_file_path, max_length=200, null=True, blank=True)


class RollCall(models.Model):
    FLAG_ARRIVAL = 1
    FLAG_DEPARTURE = 2
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    date = jmodels.jDateField()
    arrival = models.TimeField(null=True, blank=True)
    departure = models.TimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=17, decimal_places=14, verbose_name='عرض جغرافیایی', null=True, blank=True)
    longitude = models.DecimalField(max_digits=17, decimal_places=14, verbose_name='طول جغرافیایی', null=True, blank=True)
