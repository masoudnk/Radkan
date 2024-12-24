from django import forms

from employer.models import Employer,Employee


class EmployerForm(forms.ModelForm):
    class Meta:
        model = Employer
        fields = '__all__'

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'
