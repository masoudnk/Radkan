# Generated by Django 5.1.4 on 2025-01-29 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employer', '0012_rename_employee_project_employees'),
    ]

    operations = [
        migrations.AddField(
            model_name='employer',
            name='city',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='employer',
            name='district',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='employer',
            name='province',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
