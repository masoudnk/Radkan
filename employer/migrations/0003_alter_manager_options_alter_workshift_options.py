# Generated by Django 5.0.2 on 2025-01-11 09:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('employer', '0002_alter_attendancedevice_is_online_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='manager',
            options={},
        ),
        migrations.AlterModelOptions(
            name='workshift',
            options={'permissions': (('view_report', 'Can view report'),)},
        ),
    ]
