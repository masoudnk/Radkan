import django.contrib.auth.password_validation as validators
from django.contrib.auth.hashers import make_password
from django.core import exceptions
from rest_framework import serializers

from .models import *


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ("name", "codename")


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = "__all__"


class EmployerProfileOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = "__all__"


class EmployerProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = (
            "national_code",
            # "image",
            "personality",
            "birth_date",
            "phone",
            "postal_code",
            "address",
            "referrer",
            "company_name",
            "legal_entity_type",
            "company_registration_date",
            "company_registration_number",
            "branch_name",
            "economical_code",
        )


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = "__all__"


class TicketSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketSection
        fields = "__all__"


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        exclude = ()


class TicketOutputSerializer(serializers.ModelSerializer):
    section = TicketSectionSerializer()

    class Meta:
        model = Ticket
        exclude = ("user",)


class EmployerLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()


class ResetPasswordRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResetPasswordRequest
        exclude = ()


class RegisterEmployerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    accepted_rules = serializers.BooleanField(write_only=True)

    def validate(self, data):
        # user = User(**data)
        password = data.get('password')
        errors = dict()
        try:
            validators.validate_password(password=password, )
        except exceptions.ValidationError as e:
            errors['password'] = list(e.messages)
        if errors:
            raise serializers.ValidationError(errors)
        return super(RegisterEmployerSerializer, self).validate(data)

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super(RegisterEmployerSerializer, self).create(validated_data)

    class Meta:
        model = Employer
        fields = ("password", "email", "username", "mobile", "accepted_rules")


class WorkplaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workplace
        exclude = ()


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        exclude = ()


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        exclude = ()


class WorkCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCategory
        exclude = ()


class WorkCategoryOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCategory
        exclude = ("employer",)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        exclude = ()


class ProjectOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        exclude = ("employer",)


class HolidayOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        exclude = ("employer",)


class WorkplaceOutputSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    province = ProvinceSerializer(read_only=True)

    class Meta:
        model = Workplace
        exclude = ("employer",)


class EmployeeOutputSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    province = ProvinceSerializer(read_only=True)

    class Meta:
        model = Employee
        exclude = ("employer_id", "password")


class RadkanMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadkanMessage
        exclude = ()


class RadkanMessageOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadkanMessage
        exclude = ("employer",)


class WorkPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkPolicy
        exclude = ()


class WorkPolicyOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkPolicy
        exclude = ("employer",)


class EarnedLeavePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = EarnedLeavePolicy
        exclude = ()


class EarnedLeavePolicyOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = EarnedLeavePolicy
        exclude = ("employer",)


class SickLeavePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = SickLeavePolicy
        exclude = ()


class SickLeavePolicyOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = SickLeavePolicy
        exclude = ("employer",)


class OvertimePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = OvertimePolicy
        exclude = ()


class OvertimePolicyOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = OvertimePolicy
        exclude = ("employer",)


class ManualTrafficPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ManualTrafficPolicy
        exclude = ()


class ManualTrafficPolicyOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManualTrafficPolicy
        exclude = ("employer",)


class WorkMissionPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkMissionPolicy
        exclude = ()


class WorkMissionPolicyOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkMissionPolicy
        exclude = ("employer",)


class EmployeeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeRequest
        exclude = ()


class EmployeeRequestOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeRequest
        exclude = ("employer",)


class EmployeeRequestCategoryOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkMissionPolicy
        exclude = ("employer",)


class WorkShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShift
        exclude = ()


class WorkShiftOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShift
        exclude = ("employer",)


class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manager
        exclude = ()


class ManagerOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manager
        exclude = ("employer_id",)


class WorkShiftPlanListSerializer(serializers.ListSerializer):
    # def create(self, validated_data):
    #     result = [self.child.create(attrs) for attrs in validated_data]
    #     try:
    #         self.child.Meta.model.objects.bulk_create(result)
    #     except IntegrityError as e:
    #         raise ValidationError(e)
    #     return result
    def create(self, validated_data):
        books = [WorkShiftPlan(**item) for item in validated_data]
        return WorkShiftPlan.objects.bulk_create(books)

    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        plans_mapping = {plan.id: plan for plan in instance}
        data_mapping = {item['id']: item for item in validated_data}

        # Perform creations and updates.
        ret = []
        for plan_id, data in data_mapping.items():
            plan = plans_mapping.get(plan_id, None)
            # if plan is None:
            #     ret.append(self.child.create(data))
            # else:
            if plan is not None:
                ret.append(self.child.update(plan, data))

        # Perform deletions.
        # for plan_id, plan in plans_mapping.items():
        #     if plan_id not in data_mapping:
        #         plan.delete()

        return ret


class WorkShiftPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShiftPlan
        exclude = ()


class WorkShiftPlanUpdateSerializer(serializers.ModelSerializer):
    modifier = serializers.HiddenField(default=serializers.CurrentUserDefault())
    id = serializers.IntegerField()

    class Meta:
        model = WorkShiftPlan
        exclude = ()
        list_serializer_class = WorkShiftPlanListSerializer


class WorkShiftPlanOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShiftPlan
        exclude = ("employer",)


class AbsenteesSerializer(serializers.ModelSerializer):
    full_name=serializers.CharField(source="get_full_name")

    class Meta:
        model = Employee
        exclude = ("personnel_code","full_name")


class AttendeesSerializer(serializers.ModelSerializer):
    employee_code = serializers.CharField(source="employee.personnel_code")
    employee_name = serializers.CharField(source="employee.get_full_name")
    employee_workplace = serializers.CharField(source="employee.workplace")
    time = serializers.TimeField(source="arrival", format="%H:%M")

    class Meta:
        model = RollCall
        fields = ("employee_code", "employee_name", "employee_workplace", "time")
