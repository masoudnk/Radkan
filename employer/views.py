from datetime import timedelta

from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404, get_list_or_404
from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes, api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from employer.serializers import *

POST_METHOD_STR = "POST"
GET_METHOD_STR = "GET"
PUT_METHOD_STR = "PUT"


@api_view([GET_METHOD_STR])
def get_user_permissions(request):
    if request.user.is_superuser:
        permissions = Permission.objects.all()
    else:
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
    has_changed = False
    if "national_code" in request.data:
        e.national_code = request.data["national_code"]
        has_changed = True
    if "image" in request.data:
        e.image = request.FILES["image"]
        has_changed = True
    if "personality" in request.data:
        e.personality = request.data["personality"]
        has_changed = True
    if "birth_date" in request.data:
        e.birth_date = request.data["birth_date"]
        has_changed = True
    if "phone" in request.data:
        e.phone = request.data["phone"]
        has_changed = True
    if "postal_code" in request.data:
        e.postal_code = request.data["postal_code"]
        has_changed = True
    if "address" in request.data:
        e.address = request.data["address"]
        has_changed = True
    if "referrer" in request.data:
        e.referrer = request.data["referrer"]
        has_changed = True
    if "company_name" in request.data:
        e.company_name = request.data["company_name"]
        has_changed = True
    if "legal_entity_type" in request.data:
        e.legal_entity_type = request.data["legal_entity_type"]
        has_changed = True
    if "company_registration_date" in request.data:
        e.company_registration_date = request.data["company_registration_date"]
        has_changed = True
    if "company_registration_number" in request.data:
        e.company_registration_number = request.data["company_registration_number"]
        has_changed = True
    if "branch_name" in request.data:
        e.branch_name = request.data["branch_name"]
        has_changed = True
    if "economical_code" in request.data:
        e.economical_code = request.data["economical_code"]
        has_changed = True

    if has_changed:
        e.save()
    return Response({"msg": "saved" if has_changed else "no change",
                     "info": EmployerProfileOutputSerializer(e).data}, status=status.HTTP_200_OK)


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


@api_view([POST_METHOD_STR])
def create_employee(request):
    cpy_data = request.data.copy()
    cpy_data["employer_id"] = request.user.id
    ser = EmployeeSerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(EmployeeOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


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
def get_workplaces_list(request):
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


@api_view([GET_METHOD_STR])
def get_work_shift_plans_list(request):
    shift = get_object_or_404(WorkShift, employer=request.user.id, id=request.data.get("work_shift_id"))
    ser = WorkShiftPlanOutputSerializer(shift.workshiftplan_set.all(), many=True)
    return Response(ser.data, status=status.HTTP_200_OK)
