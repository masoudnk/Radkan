from datetime import timedelta

from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django.shortcuts import get_object_or_404, get_list_or_404
from django.utils.timezone import now
from excel_response import ExcelResponse
from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes, api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from employer.serializers import *

POST_METHOD_STR = "POST"
GET_METHOD_STR = "GET"
PUT_METHOD_STR = "PUT"
DELETE_METHOD_STR = "DELETE"


@api_view([POST_METHOD_STR, GET_METHOD_STR, PUT_METHOD_STR])
def test(request):
    print(
        Permission.objects.filter(codename__in=request.data.get("permissions")))
    return Response("ok")


@api_view([GET_METHOD_STR])
def get_permissions(request):
    permissions = Permission.objects.filter(content_type__app_label="employer")
    return Response(PermissionSerializer(permissions, many=True).data, status=status.HTTP_200_OK)


@api_view([GET_METHOD_STR])
def get_user_permissions(request):
    # if request.user.is_superuser:
    #     permissions = Permission.objects.all()
    # else:
    permissions = request.user.user_permissions.all() | Permission.objects.filter(group__user=request.user)
    return Response(PermissionSerializer(permissions, many=True).data, status=status.HTTP_200_OK)
    # list(set(chain(user.user_permissions.filter(content_type=ctype).values_list('codename', flat=True),
    #                Permission.objects.filter(group__user=user, content_type=ctype).values_list('codename', flat=True))))


# class LoginEmployer(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         ser = EmployerLoginSerializer(request.POST)
#         if ser.is_valid():
#             vd = ser.validated_data
#             user = EoP.authenticate(request, username=vd['email'], password=vd['password'])
#             if user is not None:
#                 login(request, user)
#                 return redirect('core:home')
#         return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
@api_view([POST_METHOD_STR])
@authentication_classes([])
@permission_classes([])
def change_password(request):
    mobile = request.POST.get('mobile')
    # todo think about how council such sensitive information
    #  user=get_object_or_404(User,(Q(email=email_or_mobile)|Q(mobile=email_or_mobile)))
    # user=get_object_or_404(User,(Q(email=email_or_mobile)|Q(mobile=email_or_mobile)))
    user = get_object_or_404(User, mobile=request.POST.get('mobile'))
    request_list = user.resetpasswordrequest_set.filter(active=True, request_date__gte=now() - timedelta(hours=1))
    if request_list.exists():
        active_request = request_list.filter(code=request.POST.get('code'))
        if active_request.exists():
            if len(active_request) == 1:
                active_request[0].active = False
                active_request[0].save()
                return Response({"msg": "password changed"}, status=status.HTTP_200_OK)

    return Response({"msg": "multiple or unacceptable requests"}, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
@authentication_classes([])
@permission_classes([])
def create_password_reset_request(request):
    mobile = request.POST.get('mobile')
    # todo think about how council such sensitive information
    # user=get_object_or_404(User,(Q(email=email_or_mobile)|Q(mobile=email_or_mobile)))
    user = get_object_or_404(User, mobile=request.POST.get('mobile'))
    ser = ResetPasswordRequestSerializer(data={"user": user.id})
    if ser.is_valid():
        ser.save()
        # todo send sms to user
        return Response({"msg": "created"}, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


def get_user_or_none(mobile=None, password=None):
    try:
        user = User.objects.get(mobile=mobile)
        if check_password(password, user.password):
            return user

    except User.DoesNotExist:
        pass
    return None


@api_view([POST_METHOD_STR])
@authentication_classes([])
@permission_classes([])
def employer_login(request):
    user = get_user_or_none(request.POST.get('mobile'), request.POST.get('password'))
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            # 'refresh': str(refresh),
            'access': str(refresh.access_token), }, status=status.HTTP_200_OK)
    return Response({"msg": "invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)


@api_view([GET_METHOD_STR])
def get_employer_profile(request):
    employer = get_object_or_404(Employer, id=request.user.id)
    ser = EmployerProfileOutputSerializer(employer)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([PUT_METHOD_STR])
def update_employer_info(request):
    e = Employer.objects.get(id=request.user.id)
    ser = EmployerProfileUpdateSerializer(e, data=request.data, partial=True)
    if ser.is_valid():
        e = ser.save()
    return Response({"msg": "saved", "info": EmployerProfileOutputSerializer(e).data}, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
@authentication_classes([])
@permission_classes([])
def create_employer(request):
    # todo handle regex for mobile numbers only
    # phone_number = request.POST.get('mobile')
    # pattern = r'/((0?9)|(\+?989))\d{2}\W?\d{3}\W?\d{4}/g'
    # if not re.match(pattern, phone_number):
    #     return Response({"msg": "شماره موبایل نادرست است"}, status=status.HTTP_400_BAD_REQUEST)
    ser = RegisterEmployerSerializer(data=request.data)
    if ser.is_valid():
        ser.save()
        return Response(ser.data, status=status.HTTP_200_OK)
    else:
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
def create_work_place(request):
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    ser = WorkplaceSerializer(data=cpy_data)
    if ser.is_valid():
        w = ser.save()
        return Response(WorkplaceOutputSerializer(instance=w).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([GET_METHOD_STR])
def get_workplaces_list(request):
    workplaces_list = get_list_or_404(Workplace, employer=request.user)
    ser = WorkplaceOutputSerializer(workplaces_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([GET_METHOD_STR])
def get_workplaces_excel(request):
    workplaces_list = get_list_or_404(Workplace, employer=request.user)
    data = [["name", "province", "city", "address", "radius", "latitude", "longitude", "BSSID"]]
    for fin in workplaces_list:
        data.append([fin.name, fin.province.name, fin.city.name, fin.address, fin.radius, fin.latitude, fin.longitude, fin.BSSID])
    return ExcelResponse(data, 'workplaces')


@api_view([GET_METHOD_STR])
def search_workplaces(request):
    name = request.GET.get('name')
    city = request.GET.get('city')
    if name and city:
        result = Workplace.objects.filter(Q(name__icontains=name) | Q(city__name__icontains=city), employer=request.user, )
    elif name:
        result = Workplace.objects.filter(employer=request.user, name__icontains=name)
    elif city:
        result = Workplace.objects.filter(employer=request.user, city__name__icontains=city)
    else:
        return Response({"msg": "invalid name or city"}, status=status.HTTP_400_BAD_REQUEST)
    ser = WorkplaceOutputSerializer(result, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([DELETE_METHOD_STR])
def delete_workplace(request, oid):
    o = get_object_or_404(Workplace, employer=request.user, id=oid)
    o.delete()
    return Response({"msg": "DELETED"}, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
def create_employee(request):
    cpy_data = request.data.copy()
    cpy_data["employer_id"] = request.user.id
    ser = EmployeeSerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(EmployeeOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([GET_METHOD_STR])
def get_employees_excel(request):
    data_list = get_list_or_404(Employee, employer_id=request.user.id)
    data = [["mobile", "first_name", "last_name", "national_code", "personnel_code", "workplace", "work_policy", "work_shift", "shift_start_date", "shift_end_date"]]
    for fin in data_list:
        data.append([str(fin.mobile), fin.first_name, fin.last_name, fin.national_code, fin.personnel_code,
                     fin.workplace.name, fin.work_policy.name, fin.work_shift.name,
                     fin.shift_start_date.strftime("%Y-%m-%d"), fin.shift_end_date.strftime("%Y-%m-%d")])
    return ExcelResponse(data, 'employees')


@api_view([GET_METHOD_STR])
def search_employees(request):
    first_name = request.GET.get('name')
    last_name = request.GET.get('last_name')
    personnel_code = request.GET.get('personnel_code')
    if not first_name and not last_name and not personnel_code:
        return Response({"msg": "invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
    result = Employee.objects.filter(employer_id=request.user.id)
    if first_name:
        result = result.filter(first_name__icontains=first_name)
    if last_name:
        result = result.filter(last_name__icontains=last_name)
    if personnel_code:
        result = result.filter(personnel_code__icontains=personnel_code)
    ser = EmployeeOutputSerializer(result, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([GET_METHOD_STR])
def get_employees_list(request):
    employees_list = get_list_or_404(Employee, employer_id=request.user.id)
    ser = EmployeeOutputSerializer(employees_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
def create_holiday(request):
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    ser = HolidaySerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(HolidayOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([GET_METHOD_STR])
def get_holidays_list(request):
    holidays_list = get_list_or_404(Holiday, employer=request.user)
    ser = HolidayOutputSerializer(holidays_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
def create_work_category(request):
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    ser = WorkCategorySerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(WorkCategoryOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([GET_METHOD_STR])
def get_work_category_list(request):
    work_categories_list = get_list_or_404(WorkCategory, employer=request.user)
    ser = HolidayOutputSerializer(work_categories_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
def create_project(request):
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    ser = ProjectSerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(ProjectOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([GET_METHOD_STR])
def get_projects_list(request):
    projects_list = get_list_or_404(Project, employer=request.user)
    ser = ProjectOutputSerializer(projects_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
def create_radkan_message(request):
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    ser = RadkanMessageSerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(RadkanMessageOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([GET_METHOD_STR])
def get_radkan_messages_list(request):
    radkan_messages_list = get_list_or_404(RadkanMessage, employer=request.user)
    ser = ProjectOutputSerializer(radkan_messages_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([GET_METHOD_STR])
def get_provinces(request):
    provinces = Province.objects.all()
    ser = ProvinceSerializer(provinces, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([GET_METHOD_STR])
def get_cities(request):
    cities = get_list_or_404(City, parent_id=request.GET.get('province_id'))
    ser = CitySerializer(cities, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([GET_METHOD_STR])
def get_ticket_sections_list(request):
    ser = TicketSectionSerializer(TicketSection.objects.all(), many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
def create_ticket(request):
    cpy_data = request.data.copy()
    cpy_data["user"] = request.user.id
    ser = TicketSerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(TicketOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([GET_METHOD_STR])
def get_tickets_list(request):
    ser = TicketOutputSerializer(request.user.ticket_set.all(), many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
def create_employee_request(request):
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    ser = EmployeeRequestSerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(EmployeeRequestOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)



def employee_requests_filter(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    category = request.GET.get('category')
    employee = request.GET.get('employee_id')
    if not from_date and not to_date and not category and not employee:
        return Response({"msg": "invalid parameter"}, status=status.HTTP_400_BAD_REQUEST)
    result = EmployeeRequest.objects.filter(employer_id=request.user.id)
    if from_date:
        result = result.filter(start_date__gte=from_date)
    if to_date:
        result = result.filter(end_date__lte=to_date)
    if category:
        result = result.filter(category=category)
    if employee:
        result = result.filter(employee_id=employee)
    return result


@api_view([GET_METHOD_STR])
def search_employee_requests(request):
    result = employee_requests_filter(request)
    ser = EmployeeOutputSerializer(result, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)

@api_view([GET_METHOD_STR])
def get_employee_requests_excel(request):
    data_list = employee_requests_filter(request)
    data = [["category", "employee", "start_date", "end_date", "registration_date", "action", ]]
    for fin in data_list:
        data.append([fin.category.name, fin.employee.get_full_name(), fin.start_date.strftime("%Y-%m-%d"), fin.end_date.strftime("%Y-%m-%d"),
                     fin.registration_date.strftime("%Y-%m-%d"), fin.get_action_display(), ])
    return ExcelResponse(data, 'employees')


@api_view([GET_METHOD_STR])
def get_employee_requests_list(request):
    ser = TicketOutputSerializer(request.user.ticket_set.all(), many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
def create_work_shift(request):
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    ser = WorkShiftSerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(WorkShiftOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([GET_METHOD_STR])
def search_work_shift(request):
    name = request.GET.get('name')
    if name is None:
        return Response({'error': '"name" is required'}, status=status.HTTP_400_BAD_REQUEST)
    result = WorkShift.objects.filter(employer=request.user, name__icontains=name)
    ser = WorkShiftOutputSerializer(result, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([DELETE_METHOD_STR])
def delete_work_shift(request, oid):
    o = get_object_or_404(WorkShift, employer=request.user, id=oid)
    o.delete()
    return Response({"msg": "DELETED"}, status=status.HTTP_200_OK)


@api_view([GET_METHOD_STR])
def get_work_shifts_list(request):
    shifts = WorkShift.objects.filter(employer=request.user.id)
    ser = WorkShiftOutputSerializer(shifts, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([GET_METHOD_STR])
def get_work_shift_plan_type_choices(request):
    data = {}
    for row in WorkShiftPlan.plan_type_choices:
        data[row[0]] = row[1]
    return Response(data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
def create_work_shift_plan(request):
    cpy_data = request.data.copy()
    is_many = False
    if isinstance(request.data, list):
        is_many = True
        for item in cpy_data:
            item["employer"] = request.user.id
    else:
        cpy_data["employer"] = request.user.id

    ser = WorkShiftPlanSerializer(data=cpy_data, many=is_many)
    if ser.is_valid():
        e = ser.save()
        return Response(WorkShiftPlanOutputSerializer(e, many=is_many).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([PUT_METHOD_STR])
def update_work_shift_plan(request):
    cpy_data = request.data.copy()
    for item in cpy_data:
        item["employer"] = request.user.id
    work_shift_plans = get_list_or_404(WorkShiftPlan, employer_id=request.user.id, work_shift_id=cpy_data[0]["work_shift"])
    ser = WorkShiftPlanUpdateSerializer(data=cpy_data, instance=work_shift_plans, many=True)
    if ser.is_valid():
        e = ser.save()
        return Response(WorkShiftPlanOutputSerializer(e, many=True).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([GET_METHOD_STR])
def get_work_shift_plans_list(request):
    shift = get_object_or_404(WorkShift, employer=request.user.id, id=request.data.get("work_shift_id"))
    ser = WorkShiftPlanOutputSerializer(shift.workshiftplan_set.all(), many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
def create_manager(request):
    cpy_data = request.data.copy()
    cpy_data["employer_id"] = request.user.id
    ser = ManagerSerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        perms = Permission.objects.filter(codename__in=request.data.get("permissions")).values_list("id", flat=True)
        e.user_permissions.add(*perms)
        return Response(ManagerOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([GET_METHOD_STR])
def get_employer_dashboard(request):
    shifts = WorkShiftPlan.objects.filter(date=now()).values_list("work_shift", flat=True)
    employees = Employee.objects.filter(work_shift__in=shifts).distinct()
    # todo write aggregations for these queries
    roll_calls = RollCall.objects.filter(date=now(), arrival__lte=now(), departure__isnull=True, employee__in=employees)
    attendees = employees.filter(id__in=roll_calls.values_list("employees", flat=True))
    absentees = employees.exclude(attendees)

    attendees_ser = AttendeesSerializer(attendees, many=True)
    absentees_ser = AbsenteesSerializer(absentees, many=True)
    return Response({"attendees": attendees_ser.data, "absentees": absentees_ser.data, }, status=status.HTTP_200_OK)
