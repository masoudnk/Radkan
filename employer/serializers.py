import django.contrib.auth.password_validation as validators
from django.contrib.auth.hashers import make_password
from django.core import exceptions
from django_jalali.serializers.serializerfield import JDateField
from rest_framework import serializers

from .models import *
from .utilities import national_code_validation, DATE_TIME_FORMAT_STR


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ("name", "codename")


class TicketSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketSection
        fields = "__all__"


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = (
            "user",
            "title",
            "section",
            "description",
            "attachment",
        )


class TicketConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketConversation
        exclude = ()


class TicketListOutputSerializer(serializers.ModelSerializer):
    section = TicketSectionSerializer()
    last_update = serializers.SerializerMethodField("get_last_update")

    def get_last_update(self, obj):
        if obj.ticketconversation_set.exists():
            return obj.ticketconversation_set.last().date_time.strftime(DATE_TIME_FORMAT_STR)
        return obj.date_time.strftime(DATE_TIME_FORMAT_STR)

    class Meta:
        model = Ticket
        exclude = ("user",)


class TicketDetailOutputSerializer(serializers.ModelSerializer):
    section = TicketSectionSerializer()
    conversations = serializers.SerializerMethodField("get_conversations")

    def get_conversations(self, obj):
        return TicketConversationSerializer(obj.ticketconversation_set.all(), many=True).data

    class Meta:
        model = Ticket
        exclude = ()


class EmployerLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()


class ResetPasswordRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResetPasswordRequest
        exclude = ()


class LegalEntityTypeOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalEntityType
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


class EmployeeSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    shift_start_date = JDateField()
    shift_end_date = JDateField()

    # employer_id  = serializers.HiddenField(default=serializers.CurrentUserDefault().id)

    def validate(self, data):
        password = data.get('password')
        errors = dict()
        try:
            validators.validate_password(password=password, )
        except exceptions.ValidationError as e:
            errors['password'] = list(e.messages)
        if errors:
            raise serializers.ValidationError(errors)
        return super(EmployeeSerializer, self).validate(data)

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super(EmployeeSerializer, self).create(validated_data)

    class Meta:
        model = Employee
        fields = (
            "employer_id",
            "password",
            "username",
            "mobile",
            "registration_date",
            "first_name",
            "last_name",
            "national_code",
            "personnel_code",
            "shift_start_date",
            "shift_end_date",
            "workplace",
            "work_policy",
            "work_shift",
        )


class EmployerProfileUpdateSerializer(serializers.ModelSerializer):

    def validate(self, data):
        errors = dict()
        try:
            national_code_validation(data.get('national_code'))
        except exceptions.ValidationError as e:
            errors["national_code"] = list(e.messages)
        if errors:
            raise serializers.ValidationError(errors)
        return super(EmployerProfileUpdateSerializer, self).validate(data)

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
            # fixme handle adding referrer
            #  "referrer",
            "company_name",
            "legal_entity_type",
            "company_registration_date",
            "company_registration_number",
            "branch_name",
            "economical_code",
            "is_male",

            "email_login_successful",
            "email_login_failed",
            "email_change_password",
            "email_employee_login",
            "email_employee_logout",

        )


class EmployerProfileOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = EmployerProfileUpdateSerializer.Meta.fields + (
            "username",
            "mobile",
        )


class WorkplaceListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        books = [Workplace(**item) for item in validated_data]
        return Workplace.objects.bulk_create(books)

    # def update(self, instance, validated_data):
    #     # Maps for id->instance and id->data item.
    #     plans_mapping = {plan.id: plan for plan in instance}
    #     data_mapping = {item['id']: item for item in validated_data}
    #     ret = []
    #     for plan_id, data in data_mapping.items():
    #         plan = plans_mapping.get(plan_id, None)
    #         if plan is not None:
    #             ret.append(self.child.update(plan, data))
    #     return ret


class WorkplaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workplace
        exclude = ()
        list_serializer_class = WorkplaceListSerializer


class HolidaySerializer(serializers.ModelSerializer):
    date = JDateField()

    class Meta:
        model = Holiday
        exclude = ()


class WorkCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCategory
        exclude = ()


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
    class Meta:
        model = Workplace
        exclude = ("employer",)


class EmployeeDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        exclude = ("employer_id", "password")


class RadkanMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadkanMessage
        exclude = ()


class RadkanMessageOutputSerializer(serializers.ModelSerializer):
    seen_contacts = serializers.SerializerMethodField("get_seen_contacts")

    def get_seen_contacts(self, obj):
        views = obj.radkanmessageviewinfo_set.all().count()
        all_employees = obj.employees.all().count()
        return "{}({})".format(all_employees, views)

    class Meta:
        model = RadkanMessage
        exclude = ("employer",)


class RollCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = RollCall
        exclude = ()


class RollCallOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = RollCall
        exclude = ("employee",)


class WorkPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkPolicy
        exclude = ()


class WorkPolicyOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkPolicy
        fields = ("name", "description",)


class EarnedLeavePolicySerializer(serializers.ModelSerializer):
    def validate(self, data):
        errors = dict()
        maximum_hour_per_year = int(data["maximum_hour_per_year"])
        maximum_minute_per_year = int(data["maximum_minute_per_year"])
        year_total = (maximum_hour_per_year * 60) + maximum_minute_per_year

        maximum_hour_per_month = int(data["maximum_hour_per_month"])
        maximum_minute_per_month = int(data["maximum_minute_per_month"])
        month_total = (maximum_hour_per_month * 60) + maximum_minute_per_month
        if month_total > year_total:
            errors["month_total"] = "مقدار اضافه کاری ماهانه بیشتر از اضافه کاری کل سال است"

        maximum_earned_leave_for_next_year_hour = int(data["maximum_earned_leave_for_next_year_hour"])
        maximum_earned_leave_for_next_year_minutes = int(data["maximum_earned_leave_for_next_year_minutes"])
        next_year_total = (maximum_earned_leave_for_next_year_hour * 60) + maximum_earned_leave_for_next_year_minutes

        if next_year_total > year_total:
            errors["next_year_total"] = "مقدار مرخصی قابل انتقال به سال بعد بیشتر از مرخصی کل سال است"

        if int(data['maximum_daily_request_per_year']) < int(data['maximum_daily_request_per_month']):
            errors["maximum_daily_request_per_month"] = "تعداد درخواست مرخصی روزانه ماهانه بیشتر از سالانه است"
        if int(data['maximum_hourly_request_per_year']) < int(data['maximum_hourly_request_per_month']):
            errors["maximum_hourly_request_per_year"] = "تعداد درخواست مرخصی ساعتی ماهانه بیشتر از سالانه است"

        if errors:
            raise serializers.ValidationError(errors)
        return super(EarnedLeavePolicySerializer, self).validate(data)

    class Meta:
        model = EarnedLeavePolicy
        exclude = ()


class EarnedLeavePolicyOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = EarnedLeavePolicy
        exclude = ("employer",)


class SickLeavePolicySerializer(serializers.ModelSerializer):
    def validate(self, data):
        errors = dict()
        maximum_hour_per_year = int(data["maximum_hour_per_year"])
        maximum_minute_per_year = int(data["maximum_minute_per_year"])
        year_total = (maximum_hour_per_year * 60) + maximum_minute_per_year

        maximum_hour_per_month = int(data["maximum_hour_per_month"])
        maximum_minute_per_month = int(data["maximum_minute_per_month"])
        month_total = (maximum_hour_per_month * 60) + maximum_minute_per_month

        if month_total > year_total:
            errors["month_total"] = "مقدار مرخصی ماهانه بیشتر از مرخصی کل سال است"

        if int(data['maximum_daily_request_per_year']) < int(data['maximum_daily_request_per_month']):
            errors["maximum_daily_request_per_month"] = "تعداد درخواست مرخصی روزانه ماهانه بیشتر از سالانه است"
        if int(data['maximum_hourly_request_per_year']) < int(data['maximum_hourly_request_per_month']):
            errors["maximum_hourly_request_per_year"] = "تعداد درخواست مرخصی ساعتی ماهانه بیشتر از سالانه است"

        if errors:
            raise serializers.ValidationError(errors)
        return super(SickLeavePolicySerializer, self).validate(data)

    class Meta:
        model = SickLeavePolicy
        exclude = ()


class SickLeavePolicyOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = SickLeavePolicy
        exclude = ("employer",)


class OvertimePolicySerializer(serializers.ModelSerializer):
    def validate(self, data):
        errors = dict()
        maximum_hour_per_year = int(data["maximum_hour_per_year"])
        maximum_minute_per_year = int(data["maximum_minute_per_year"])
        year_total = (maximum_hour_per_year * 60) + maximum_minute_per_year

        maximum_hour_per_month = int(data["maximum_hour_per_month"])
        maximum_minute_per_month = int(data["maximum_minute_per_month"])
        month_total = (maximum_hour_per_month * 60) + maximum_minute_per_month

        if month_total > year_total:
            errors["month_total"] = "مقدار اضافه کاری ماهانه بیشتر از اضافه کاری کل سال است"

        if int(data['maximum_daily_request_per_year']) < int(data['maximum_daily_request_per_month']):
            errors["maximum_daily_request_per_month"] = "تعداد درخواست مرخصی روزانه ماهانه بیشتر از سالانه است"
        if int(data['maximum_hourly_request_per_year']) < int(data['maximum_hourly_request_per_month']):
            errors["maximum_hourly_request_per_year"] = "تعداد درخواست مرخصی ساعتی ماهانه بیشتر از سالانه است"

        if errors:
            raise serializers.ValidationError(errors)
        return super(OvertimePolicySerializer, self).validate(data)

    class Meta:
        model = OvertimePolicy
        exclude = ()


class OvertimePolicyOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = OvertimePolicy
        exclude = ("employer",)


class ManualTrafficPolicySerializer(serializers.ModelSerializer):
    def validate(self, data):
        errors = dict()
        if int(data['maximum_per_year']) < int(data['maximum_per_month']):
            errors["maximum_per_year"] = "تعداد درخواست تردد دستی ماهانه بیشتر از سالانه است"

        if errors:
            raise serializers.ValidationError(errors)
        return super(ManualTrafficPolicySerializer, self).validate(data)

    class Meta:
        model = ManualTrafficPolicy
        exclude = ()


class ManualTrafficPolicyOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManualTrafficPolicy
        exclude = ("employer",)


class WorkMissionPolicySerializer(serializers.ModelSerializer):
    def validate(self, data):
        errors = dict()
        maximum_hour_per_year = int(data["maximum_hour_per_year"])
        maximum_minute_per_year = int(data["maximum_minute_per_year"])
        year_total = (maximum_hour_per_year * 60) + maximum_minute_per_year

        maximum_hour_per_month = int(data["maximum_hour_per_month"])
        maximum_minute_per_month = int(data["maximum_minute_per_month"])
        month_total = (maximum_hour_per_month * 60) + maximum_minute_per_month
        if month_total > year_total:
            errors["month_total"] = "مقدار ماموریت ماهانه بیشتر از سال است"

        if int(data['maximum_daily_request_per_year']) < int(data['maximum_daily_request_per_month']):
            errors["maximum_daily_request_per_month"] = "تعداد درخواست ماموریت روزانه ماهانه بیشتر از سالانه است"
        if int(data['maximum_hourly_request_per_year']) < int(data['maximum_hourly_request_per_month']):
            errors["maximum_hourly_request_per_year"] = "تعداد درخواست ماموریت ساعتی ماهانه بیشتر از سالانه است"

        if errors:
            raise serializers.ValidationError(errors)
        return super(WorkMissionPolicySerializer, self).validate(data)

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
    category_display = serializers.CharField(source='get_category_display')
    action_display = serializers.CharField(source='get_action_display')
    manual_traffic_type_display = serializers.CharField(source='get_manual_traffic_type_display')

    class Meta:
        model = EmployeeRequest
        exclude = ("employer",)
        read_only_fields = ('category_display',)


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


class RTSPSerializer(serializers.ModelSerializer):
    class Meta:
        model = RTSP
        exclude = ()


class RTSPOutputSerializer(serializers.ModelSerializer):
    workplace = WorkplaceOutputSerializer(read_only=True)

    class Meta:
        model = RTSP
        exclude = ("employer",)


class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manager
        exclude = ()


class RegisterManagerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        password = data.get('password')
        errors = dict()
        try:
            validators.validate_password(password=password, )
        except exceptions.ValidationError as e:
            errors['password'] = list(e.messages)
        if errors:
            raise serializers.ValidationError(errors)
        return super(RegisterManagerSerializer, self).validate(data)

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super(RegisterManagerSerializer, self).create(validated_data)

    class Meta:
        model = Manager
        exclude = ()


class ManagerOutputSerializer(serializers.ModelSerializer):
    expiration_date = serializers.DateTimeField(format=DATE_TIME_FORMAT_STR)

    class Meta:
        model = Manager
        fields = ("expiration_date", "username", "mobile")


class WorkShiftPlanListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        books = [WorkShiftPlan(**item) for item in validated_data]
        return WorkShiftPlan.objects.bulk_create(books)

    def update(self, instance, validated_data):
        plans_mapping = {plan.id: plan for plan in instance}
        data_mapping = {item['id']: item for item in validated_data}
        ret = []
        for plan_id, data in data_mapping.items():
            plan = plans_mapping.get(plan_id, None)
            if plan is not None:
                ret.append(self.child.update(plan, data))
        return ret


class WorkShiftPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShiftPlan
        exclude = ()


class WorkShiftPlanUpdateSerializer(serializers.ModelSerializer):
    modifier = serializers.HiddenField(default=serializers.CurrentUserDefault())
    id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = WorkShiftPlan
        exclude = ()
        list_serializer_class = WorkShiftPlanListSerializer


class WorkShiftPlanOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShiftPlan
        exclude = ("employer",)


class AbsenteesSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="employee.get_full_name")
    personnel_code = serializers.CharField(source="employee.personnel_code")

    class Meta:
        model = RollCall
        fields = ("personnel_code", "full_name")


class AttendeesSerializer(serializers.ModelSerializer):
    employee_code = serializers.CharField(source="employee.personnel_code")
    employee_name = serializers.CharField(source="employee.get_full_name")
    employee_workplace = serializers.CharField(source="employee.workplace")
    time = serializers.TimeField(source="arrival", format="%H:%M")

    class Meta:
        model = RollCall
        fields = ("employee_code", "employee_name", "employee_workplace", "time")


def required(value):
    if value is None:
        raise serializers.ValidationError('This field is required')


class EmployeeRequestBaseSerializer(serializers.ModelSerializer):
    category = serializers.IntegerField(validators=[required])
    employee_id = serializers.IntegerField(validators=[required])
    description = serializers.CharField(validators=[required])
    date = serializers.CharField(validators=[required])

    class Meta:
        model = EmployeeRequest
        fields = (
            "employer",
            "category",
            "employee_id",
            "description",
            "date",
        )


class EmployeeRequestBaseManualTrafficSerializer(EmployeeRequestBaseSerializer):
    workplace_id = serializers.IntegerField(validators=[required])
    manual_traffic_type = serializers.IntegerField(validators=[required])
    date = serializers.CharField(validators=[required])

    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestBaseSerializer.Meta.fields + (
            "workplace_id",
            "date",
            "manual_traffic_type",
        )


class EmployeeRequestManualTrafficSerializer(EmployeeRequestBaseManualTrafficSerializer):
    time = serializers.CharField(validators=[required])

    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestBaseManualTrafficSerializer.Meta.fields + (
            "time",
        )


class EmployeeRequestProjectManualTrafficSerializer(EmployeeRequestBaseManualTrafficSerializer):
    project = serializers.IntegerField(validators=[required])

    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestBaseManualTrafficSerializer.Meta.fields + (
            "project",
        )


class EmployeeRequestHourlyEarnedLeaveSerializer(EmployeeRequestBaseSerializer):
    time = serializers.CharField(validators=[required])
    to_time = serializers.CharField(validators=[required])

    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestBaseSerializer.Meta.fields + (

            "to_time",
            "date",
            "time",
        )


class EmployeeRequestDailyEarnedLeaveSerializer(EmployeeRequestBaseSerializer):
    date = serializers.CharField(validators=[required])
    end_date = serializers.CharField(validators=[required])

    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestBaseSerializer.Meta.fields + (
            "end_date",
            "date",
        )


class EmployeeRequestHourlyMissionSerializer(EmployeeRequestHourlyEarnedLeaveSerializer):
    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestHourlyEarnedLeaveSerializer.Meta.fields + (
            "latitude",
            "longitude",
        )


class EmployeeRequestDailyMissionSerializer(EmployeeRequestDailyEarnedLeaveSerializer):
    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestDailyEarnedLeaveSerializer.Meta.fields + (
            "latitude",
            "longitude",
        )


class EmployeeRequestOvertimeSerializer(EmployeeRequestHourlyEarnedLeaveSerializer):
    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestHourlyEarnedLeaveSerializer.Meta.fields


class EmployeeRequestDailySickLeaveSerializer(EmployeeRequestDailyEarnedLeaveSerializer):
    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestDailyEarnedLeaveSerializer.Meta.fields + (
            "attachment",
        )


class EmployeeRequestHourlySickLeaveSerializer(EmployeeRequestHourlyEarnedLeaveSerializer):
    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestHourlyEarnedLeaveSerializer.Meta.fields + (
            "attachment",
        )


class EmployeeRequestDailyUnpaidLeaveSerializer(EmployeeRequestDailyEarnedLeaveSerializer):
    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestDailyEarnedLeaveSerializer.Meta.fields


class EmployeeRequestHourlyUnpaidLeaveSerializer(EmployeeRequestHourlyEarnedLeaveSerializer):
    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestHourlyEarnedLeaveSerializer.Meta.fields


class EmployeeRequestShiftChangeSerializer(EmployeeRequestDailyEarnedLeaveSerializer):
    other_employee = serializers.IntegerField(validators=[required])

    class Meta:
        model = EmployeeRequest
        fields = EmployeeRequestDailyEarnedLeaveSerializer.Meta.fields + (
            "other_employee",
        )


class WorkPolicyFullDetailsOutputSerializer(serializers.ModelSerializer):
    earnedleavepolicy = EarnedLeavePolicyOutputSerializer()
    sickleavepolicy = SickLeavePolicyOutputSerializer()
    overtimepolicy = OvertimePolicyOutputSerializer()
    manualtrafficpolicy = ManualTrafficPolicyOutputSerializer()
    workmissionpolicy = WorkMissionPolicyOutputSerializer()

    class Meta:
        model = WorkPolicy
        exclude = ("employer",)


class EarnedLeavePolicyUpdateSerializer(EarnedLeavePolicySerializer):
    class Meta:
        model = EarnedLeavePolicy
        exclude = ("employer", "work_policy")


class SickLeavePolicyUpdateSerializer(SickLeavePolicySerializer):
    class Meta:
        model = SickLeavePolicy
        exclude = ("employer", "work_policy")


class OvertimePolicyUpdateSerializer(OvertimePolicySerializer):
    class Meta:
        model = OvertimePolicy
        exclude = ("employer", "work_policy")


class ManualTrafficPolicyUpdateSerializer(ManualTrafficPolicySerializer):
    class Meta:
        model = ManualTrafficPolicy
        exclude = ("employer", "work_policy")


class WorkMissionPolicyUpdateSerializer(WorkMissionPolicySerializer):
    class Meta:
        model = WorkMissionPolicy
        exclude = ("employer", "work_policy")


class EmployeeOutputSerializer(serializers.ModelSerializer):
    work_policy = WorkPolicyFullDetailsOutputSerializer(read_only=True)
    work_shift = WorkShiftOutputSerializer(read_only=True)
    shift_start_date = JDateField(read_only=True)
    shift_end_date = JDateField(read_only=True)

    class Meta:
        model = Employee
        exclude = ("employer_id", "password")


class EmployeeShortOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ("id", "username", "mobile", "first_name", "last_name",)


class WorkCategoryOutputSerializer(serializers.ModelSerializer):
    employee = EmployeeShortOutputSerializer(read_only=True, many=True)
    parent_name = serializers.CharField(source="parent.name", default=None, read_only=True)

    class Meta:
        model = WorkCategory
        fields = ("id", "parent", "name", "employee", "parent_name")
