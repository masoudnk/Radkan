import phonenumber_field
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django_jalali.db import models as jmodels

from base.models import get_file_path
from employer.models import Workplace, WorkPolicy, WorkShift


# Create your models here.

class Staff(models.Model):
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
    user_name = models.CharField(max_length=255, verbose_name='نام کاربری')
    password = models.CharField(max_length=255, verbose_name='رمز عبور')
    national_code = models.CharField(max_length=250,null=True, blank=True,verbose_name="کد ملی")
    personnel_code  = models.CharField(max_length=250)
    workplace = models.ForeignKey(Workplace, on_delete=models.PROTECT)
    work_policy = models.ForeignKey(WorkPolicy, on_delete=models.PROTECT)
    work_shift  = models.ForeignKey(WorkShift, on_delete=models.PROTECT)
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
    limit_devices=models.PositiveSmallIntegerField(choices=device_choices, default=device_choices[0][0])
    interception  = models.BooleanField(default=False)

    def __str__(self):
        return self.first_name+" "+self.last_name

class StaffRequestCategory(models.Model):
    name = models.CharField(max_length=250)
class StaffRequest(models.Model):
    category = models.ForeignKey(StaffRequestCategory, on_delete=models.PROTECT)
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    registration_date = models.DateField(auto_now_add=True)
    action_choices = (
        (1,"در دست بررسی"),
        (2,"تایید شده"),
        (3,"تایید شده"),
    )
