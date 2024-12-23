import os
import uuid

from django.db import models
from django_jalali.db import models as jmodels

# Create your models here.

def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4().hex, ext)
    return os.path.join('ClientsFiles/' + uuid.uuid4().hex, filename)



class Province(models.Model):
    name = models.CharField(max_length=255, verbose_name='استان')

    class Meta:
        verbose_name = 'استان'
        verbose_name_plural = 'استان ها'

    def __str__(self):
        return self.name


class City(models.Model):
    parent = models.ForeignKey(Province, on_delete=models.CASCADE,  verbose_name='استان')
    name = models.CharField(max_length=255, verbose_name='نام')
    # latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='عرض جغرافیایی')
    # longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='طول جغرافیایی')

    class Meta:
        verbose_name = 'شهر'
        verbose_name_plural = 'شهر ها'

    def __str__(self):
        return self.name
