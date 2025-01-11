from datetime import timedelta

import openpyxl
from django.core.exceptions import PermissionDenied
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, get_list_or_404
from django.utils.timezone import now
from jdatetime import datetime
from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes, api_view
from rest_framework.response import Response

from employer.apps import get_this_app_name
from employer.serializers import *
from employer.utilities import national_code_validation, send_response_file, POST_METHOD_STR, PUT_METHOD_STR, VIEW_PERMISSION_STR, CHANGE_PERMISSION_STR, ADD_PERMISSION_STR, \
    DELETE_METHOD_STR, DELETE_PERMISSION_STR, DATE_FORMAT_STR, DATE_TIME_FORMAT_STR
from melipayamak import Api


def get_acceptable_permissions(model=Manager, filters=None):
    base_list = [WorkShift, WorkShiftPlan, Workplace, Employee, Holiday, EmployeeRequest, Project, WorkCategory,
                 WorkPolicy, ManualTrafficPolicy, OvertimePolicy, LeavePolicy, EarnedLeavePolicy, SickLeavePolicy,
                 WorkMissionPolicy, RadkanMessage]
    employer_list = [Manager, Employer, MelliSMSInfo, RTSP, ]
    if model.__name__ == Employer.__name__:
        base_list.extend(employer_list)
    model_names = [m.__name__.lower() for m in base_list]
    perms = Permission.objects.filter(content_type__model__in=model_names, content_type__app_label=get_this_app_name())
    if filters:
        perms = perms.filter(codename__in=filters)
    return perms


@api_view([POST_METHOD_STR, PUT_METHOD_STR])
def test(request, **kwargs):
    is_valid, msg = national_code_validation(request.data.get("national_code"))
    return Response({"is_valid": is_valid, "msg": msg}, status=status.HTTP_200_OK)


def check_user_permission(action, model):
    def decorator(function):
        def wrapper(request, *args, **kwargs):
            print("request.user:", request.user.id)
            # print("start o decorator:", request, args, kwargs)
            kwargs.update(request.data.copy())
            try:
                employer = Employer.objects.get(id=request.user.id, is_active=True)
                kwargs["employer"] = employer.id
            except Employer.DoesNotExist:
                try:
                    manager = Manager.objects.get(id=request.user.id, is_active=True, expiration_date__gte=now())
                    kwargs["manager"] = manager.id
                    kwargs["employer"] = manager.employer_id
                except Manager.DoesNotExist:
                    return Response({"msg": "unauthorized request"}, status=status.HTTP_401_UNAUTHORIZED)
            if action is not None and model is not None:
                if isinstance(model, str):
                    model_name = model
                else:
                    model_name = model.__name__.lower()

                perm = "{}.{}_{}".format(get_this_app_name(), action, model_name)
                if isinstance(perm, str):
                    perms = (perm,)
                else:
                    perms = perm
                if not request.user.has_perms(perms):
                    raise PermissionDenied
            # print(request, args, kwargs)
            result = function(request, *args, **kwargs)
            return result

        return wrapper

    return decorator


def send_sms():
    # todo get melli payamak info
    username = 'username'
    password = 'password'
    api = Api(username, password)
    sms = api.sms()
    to = '09123456789'
    _from = '5000...'
    text = 'تست وب سرویس ملی پیامک'
    response = sms.send(to, _from, text)


def handle_single_or_list_objects(data, user_id, serializer):
    is_many = False
    if isinstance(data, list):
        is_many = True
        for item in data:
            item["employer"] = user_id
    else:
        data["employer"] = user_id
    return serializer(data=data, many=is_many), is_many


@api_view()
@check_user_permission(None, None)
def get_permissions(request, **kwargs):
    # permissions = Permission.objects.filter(content_type__app_label=get_this_app_name())
    return Response(PermissionSerializer(get_acceptable_permissions(), many=True).data, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(None, None)
def get_user_permissions(request, **kwargs):
    permissions = request.user.user_permissions.all() | Permission.objects.filter(group__user=request.user)
    return Response(PermissionSerializer(permissions, many=True).data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
@authentication_classes([])
@permission_classes([])
def change_password(request, **kwargs):
    mobile = request.POST.get('mobile')
    password = request.data.get('password')
    try:
        validators.validate_password(password=password, )
    except exceptions.ValidationError as e:
        return Response({'password': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(mobile=mobile, is_active=True)
    except User.DoesNotExist:
        make_password(password)
        return Response({"msg": "unacceptable information"}, status=status.HTTP_400_BAD_REQUEST)
    request_list = user.resetpasswordrequest_set.filter(active=True, request_date__gte=now() - timedelta(hours=1))
    if request_list.exists():
        active_request = request_list.last()
        if active_request.code == int(request.POST.get('code')):
            user.set_password(password)
            user.save()
            active_request.active = False
            active_request.save()
            try:
                employer = Employer.objects.get(id=user.id)
                # todo send email
                # if employer.email:
                #     send_mail(
                #         "changed password",
                #         "Here is the message.",
                #         from_email=None,
                #         recipient_list=[employer.email],
                #     )
            except Employer.DoesNotExist as e:
                pass

            return Response({"msg": "password changed"}, status=status.HTTP_200_OK)
    return Response({"msg": "unacceptable information"}, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
@authentication_classes([])
@permission_classes([])
def create_password_reset_request(request, **kwargs):
    mobile = request.POST.get('mobile')
    try:
        user = get_object_or_404(User, mobile=mobile, is_active=True)
        request_list = user.resetpasswordrequest_set.filter(active=True, request_date__gte=now() - timedelta(hours=1))
        if request_list.exists():
            make_password(mobile)
            # return Response({"msg": "multiple requests is unacceptable"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            ser = ResetPasswordRequestSerializer(data={"user": user.id})
            if ser.is_valid():
                ser.save()
                # todo send sms to user
                #  send_sms()
        return Response({"msg": "created"}, status=status.HTTP_201_CREATED)

    except User.DoesNotExist:
        # conceal information
        make_password(mobile)
        return Response({"msg": "created"}, status=status.HTTP_201_CREATED)


# def get_user_or_none(mobile=None, password=None):
#     try:
#         user = User.objects.get(mobile=mobile)
#         if check_password(password, user.password):
#             return user
#
#     except User.DoesNotExist:
#         pass
#     return None


# @api_view([POST_METHOD_STR])
# @authentication_classes([])
# @permission_classes([])
# def employer_login(request,  **kwargs):
#     user = get_user_or_none(request.POST.get('mobile'), request.POST.get('password'))
#     if user is not None:
#         refresh = RefreshToken.for_user(user)
#         return Response({
#             # 'refresh': str(refresh),
#             'access': str(refresh.access_token), }, status=status.HTTP_200_OK)
#     return Response({"msg": "invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Employer)
def get_employer_profile(request, **kwargs):
    employer = get_object_or_404(Employer, id=request.user.id)
    ser = EmployerProfileOutputSerializer(employer)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, Employer)
def update_employer_info(request, **kwargs):
    e = Employer.objects.get(id=request.user.id)
    ser = EmployerProfileUpdateSerializer(e, data=request.data, partial=True)
    if ser.is_valid(raise_exception=True):
        e = ser.save()
    return Response({"msg": "saved", "info": EmployerProfileOutputSerializer(e).data}, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
@authentication_classes([])
@permission_classes([])
def create_employer(request, **kwargs):
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
@check_user_permission(ADD_PERMISSION_STR, Workplace)
def create_work_place(request, **kwargs):
    ser = WorkplaceSerializer(data=kwargs)
    if ser.is_valid():
        w = ser.save()
        return Response(WorkplaceOutputSerializer(instance=w).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
@check_user_permission(ADD_PERMISSION_STR, Workplace)
@check_user_permission(CHANGE_PERMISSION_STR, Workplace)
def import_work_places_excel(request, **kwargs):
    workbook = openpyxl.load_workbook(request.FILES["excel_file"], read_only=True)
    worksheet = workbook.active
    workplaces = []
    titles = ["name", "city", "address", "radius", "latitude", "longitude", "BSSID"]
    for row in worksheet.iter_rows(min_row=2):
        dictionary = {}
        zipped = zip(titles, row)
        for t, c in zipped:
            dictionary[t] = c.value
        workplaces.append(dictionary)
    # Unlike a normal workbook, a read-only workbook will use lazy loading. The workbook must be explicitly closed with the close() method.
    # Close the workbook after reading
    workbook.close()
    ser, is_many = handle_single_or_list_objects(workplaces, kwargs["employer"], WorkplaceSerializer)
    if ser.is_valid():
        s = ser.save()
        return Response(WorkplaceOutputSerializer(s, many=is_many).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, Workplace)
def update_work_place(request, oid, **kwargs):
    wp = get_object_or_404(Workplace, employer_id=kwargs["employer"], id=oid)
    # using output serializer to prevent change employer
    ser = WorkplaceOutputSerializer(data=request.data, instance=wp, partial=True)
    if ser.is_valid():
        w = ser.save()
        return Response(WorkplaceOutputSerializer(instance=w).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Workplace)
def get_workplaces_list(request, **kwargs):
    workplaces_list = Workplace.objects.filter(employer_id=kwargs["employer"])
    if "order_by" in kwargs:
        workplaces_list = workplaces_list.order_by(kwargs["order_by"])
    ser = WorkplaceOutputSerializer(workplaces_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Workplace)
def get_workplace(request, oid, **kwargs):
    workplaces_list = get_object_or_404(Workplace, employer_id=kwargs["employer"], id=oid)
    ser = WorkplaceOutputSerializer(workplaces_list)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Workplace)
def get_workplaces_excel(request, **kwargs):
    workplaces_list = get_list_or_404(Workplace, employer_id=kwargs["employer"])
    data = [["نام", "شهر", "آدرس", "محیط", "latitude", "longitude"]]
    for fin in workplaces_list:
        data.append([fin.name, fin.city, fin.address, fin.radius, fin.latitude, fin.longitude])
    return send_response_file(data, 'workplaces')


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Workplace)
def search_workplaces(request, **kwargs):
    name = request.GET.get('name')
    city = request.GET.get('city')
    employer = Employer.objects.get(id=kwargs["employer"])
    result = employer.workplace_set
    if name and city:
        result = result.filter(name__icontains=name, city__icontains=city)
    elif name:
        result = result.filter(employer=request.user, name__icontains=name)
    elif city:
        result = result.filter(employer=request.user, city__name__icontains=city)
    else:
        return Response({"msg": "invalid name or city"}, status=status.HTTP_400_BAD_REQUEST)
    if "order_by" in kwargs:
        result = result.order_by(kwargs["order_by"])
    ser = WorkplaceOutputSerializer(result, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([DELETE_METHOD_STR])
@check_user_permission(DELETE_PERMISSION_STR, Workplace)
def delete_workplace(request, oid, **kwargs):
    o = get_object_or_404(Workplace, employer_id=kwargs["employer"], id=oid)
    try:
        o.delete()
    except ProtectedError as e:
        return Response({"msg": "delete workplace failed: referenced through protected foreign keys"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"msg": "DELETED"}, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
@check_user_permission(ADD_PERMISSION_STR, Employee)
def create_employee(request, **kwargs):
    cpy_data = request.data.copy()
    cpy_data["employer_id"] = kwargs["employer"]
    ser = EmployeeSerializer(data=cpy_data)
    if ser.is_valid():
        # print(ser.validated_data)
        e = ser.save()
        return Response(EmployeeOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, Employee)
def update_employee(request, **kwargs):
    # cpy_data = request.data.copy()
    # cpy_data["employer_id"] = request.user.id
    employee = get_object_or_404(Employee, id=kwargs["employee_id"], employer_id=kwargs["employer"])
    ser = EmployeeSerializer(data=kwargs, instance=employee, partial=True)
    if ser.is_valid():
        e = ser.save()
        return Response(EmployeeOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Employee)
def get_employee(request, oid, **kwargs):
    employee = get_object_or_404(Employee, id=oid, employer_id=kwargs["employer"])
    return Response(EmployeeOutputSerializer(employee).data, status=status.HTTP_201_CREATED)


@api_view([DELETE_METHOD_STR])
@check_user_permission(DELETE_PERMISSION_STR, Employee)
def delete_employee(request, oid, **kwargs):
    o = get_object_or_404(Employee, employer_id=kwargs["employer"], id=oid)
    o.delete()
    return Response({"msg": "DELETED"}, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Employee)
def get_employees_excel(request, **kwargs):
    data_list = get_list_or_404(Employee, employer_id=kwargs["employer"])
    data = [["mobile", "first_name", "last_name", "national_code", "personnel_code", "workplace", "work_policy", "work_shift", "shift_start_date", "shift_end_date"]]
    for fin in data_list:
        data.append([str(fin.mobile), fin.first_name, fin.last_name, fin.national_code, fin.personnel_code,
                     fin.workplace.name, fin.work_policy.name, fin.work_shift.name,
                     fin.shift_start_date.strftime(DATE_FORMAT_STR), fin.shift_end_date.strftime(DATE_FORMAT_STR)])
    return send_response_file(data, 'employees')


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Employee)
def search_employees(request, **kwargs):
    first_name = request.GET.get('name')
    last_name = request.GET.get('last_name')
    personnel_code = request.GET.get('personnel_code')
    if not first_name and not last_name and not personnel_code:
        return Response({"msg": "invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
    result = Employee.objects.filter(employer_id=kwargs["employer"])
    if first_name:
        result = result.filter(first_name__icontains=first_name)
    if last_name:
        result = result.filter(last_name__icontains=last_name)
    if personnel_code:
        result = result.filter(personnel_code__icontains=personnel_code)
    ser = EmployeeOutputSerializer(result, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Employee)
def get_employees_list(request, **kwargs):
    employees_list = get_list_or_404(Employee, employer_id=kwargs["employer"])
    ser = EmployeeOutputSerializer(employees_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
@check_user_permission(ADD_PERMISSION_STR, Holiday)
def create_holiday(request, **kwargs):
    # cpy_data = request.data.copy()
    # cpy_data["employer"] = kwargs["employer"]
    ser = HolidaySerializer(data=kwargs)
    if ser.is_valid():
        e = ser.save()
        return Response(HolidayOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([DELETE_METHOD_STR])
@check_user_permission(DELETE_PERMISSION_STR, Holiday)
def delete_holiday(request, oid, **kwargs):
    o = get_object_or_404(Holiday, employer_id=kwargs["employer"], id=oid)
    o.delete()
    return Response({"msg": "DELETED"}, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Holiday)
def get_holidays_list(request, **kwargs):
    holidays_list = get_list_or_404(Holiday, employer_id=kwargs["employer"])
    ser = HolidayOutputSerializer(holidays_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
@check_user_permission(ADD_PERMISSION_STR, WorkCategory)
def create_work_category(request, **kwargs):
    # cpy_data = request.data.copy()
    # cpy_data["employer"] = request.user.id
    ser = WorkCategorySerializer(data=kwargs)
    if ser.is_valid():
        e = ser.save()
        return Response(WorkCategoryOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([DELETE_METHOD_STR])
@check_user_permission(DELETE_PERMISSION_STR, WorkCategory)
def delete_work_category(request, oid, **kwargs):
    o = get_object_or_404(WorkCategory, employer_id=kwargs["employer"], id=oid)
    o.delete()
    return Response({"msg": "DELETED"}, status=status.HTTP_200_OK)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, WorkCategory)
def update_work_category(request, oid, **kwargs):
    wc = get_object_or_404(WorkCategory, employer_id=kwargs["employer"], id=oid)
    ser = WorkCategoryOutputSerializer(data=request.data, instance=wc, partial=True)
    if ser.is_valid():
        e = ser.save()
        return Response(WorkCategoryOutputSerializer(e).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, WorkCategory)
def get_work_category(request, oid, **kwargs):
    wc = get_object_or_404(WorkCategory, employer_id=kwargs["employer"], id=oid)
    ser = WorkCategoryOutputSerializer(wc)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, WorkCategory)
def get_work_category_list(request, **kwargs):
    work_categories_list = get_list_or_404(WorkCategory, employer_id=kwargs["employer"])
    ser = HolidayOutputSerializer(work_categories_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
@check_user_permission(ADD_PERMISSION_STR, Project)
def create_project(request, **kwargs):
    # cpy_data = request.data.copy()
    # cpy_data["employer"] = request.user.id
    ser = ProjectSerializer(data=kwargs)
    if ser.is_valid():
        e = ser.save()
        return Response(ProjectOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([DELETE_METHOD_STR])
@check_user_permission(DELETE_PERMISSION_STR, Project)
def delete_project(request, oid, **kwargs):
    o = get_object_or_404(Project, employer_id=kwargs["employer"], id=oid)
    o.delete()
    return Response({"msg": "DELETED"}, status=status.HTTP_200_OK)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, Project)
def update_project(request, oid, **kwargs):
    wc = get_object_or_404(Project, employer_id=kwargs["employer"], id=oid)
    ser = ProjectOutputSerializer(data=request.data, instance=wc, partial=True)
    if ser.is_valid():
        e = ser.save()
        return Response(ProjectOutputSerializer(e).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Project)
def get_project(request, oid, **kwargs):
    wc = get_object_or_404(Project, employer_id=kwargs["employer"], id=oid)
    ser = ProjectOutputSerializer(wc)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Project)
def get_projects_list(request, **kwargs):
    projects_list = get_list_or_404(Project, employer_id=kwargs["employer"])
    ser = ProjectOutputSerializer(projects_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
@check_user_permission(ADD_PERMISSION_STR, RadkanMessage)
def create_radkan_message(request, **kwargs):
    # cpy_data = request.data.copy()
    # cpy_data["employer"] = request.user.id
    ser = RadkanMessageSerializer(data=kwargs)
    if ser.is_valid():
        e = ser.save()
        return Response(RadkanMessageOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, RadkanMessage)
def get_radkan_messages_list(request, **kwargs):
    radkan_messages_list = get_list_or_404(RadkanMessage, employer_id=kwargs["employer"])
    ser = ProjectOutputSerializer(radkan_messages_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, RadkanMessage)
def get_radkan_messages_view_info_list(request, oid, **kwargs):
    msg = get_object_or_404(RadkanMessage, employer_id=kwargs["employer"], id=oid)
    employees = msg.employees.all()
    views = msg.radkanmessageviewinfo_set.all()
    result = []
    for employee in employees:
        row = {"personnel_code": employee.personnel_code, "full_name": employee.get_full_name(), }
        view = views.filter(employee_id=employee.id)
        if view.exists():
            row["date"] = view[0].date_time.strftime(DATE_TIME_FORMAT_STR)
        else:
            row["date"] = None
        result.append(row)
    return Response(result, status=status.HTTP_200_OK)


@api_view()
def get_ticket_sections_list(request, **kwargs):
    ser = TicketSectionSerializer(TicketSection.objects.all(), many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
def create_ticket(request, **kwargs):
    cpy_data = request.data.copy()
    cpy_data["user"] = request.user.id
    ser = TicketSerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(TicketListOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
def create_ticket_conversation(request, oid):
    ticket = get_object_or_404(Ticket, user=request.user, id=oid)
    cpy_data = request.data.copy()
    cpy_data["user_id"] = request.user.id
    cpy_data["ticket_id"] = ticket.id
    ser = TicketConversationSerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(TicketConversationSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view()
def get_tickets_list(request, **kwargs):
    ser = TicketListOutputSerializer(request.user.ticket_set.all(), many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view()
def get_ticket(request, oid):
    ticket = get_object_or_404(Ticket, user=request.user, id=oid)
    ser = TicketDetailOutputSerializer(ticket)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([PUT_METHOD_STR])
def update_ticket_status(request, oid):
    ticket = get_object_or_404(Ticket, user=request.user, id=oid)
    ticket.active = request.data['active']
    ticket.save()
    return Response(TicketListOutputSerializer(ticket).data, status=status.HTTP_200_OK)


def manage_and_create_employee_request(cpy_data):
    category = int(cpy_data["category"])
    if category == EmployeeRequest.CATEGORY_MANUAL_TRAFFIC:
        ser = EmployeeRequestManualTrafficSerializer(data=cpy_data)
    elif category == EmployeeRequest.CATEGORY_HOURLY_EARNED_LEAVE:
        ser = EmployeeRequestHourlyEarnedLeaveSerializer(data=cpy_data)
    elif category == EmployeeRequest.CATEGORY_DAILY_EARNED_LEAVE:
        ser = EmployeeRequestDailyEarnedLeaveSerializer(data=cpy_data)
    elif category == EmployeeRequest.CATEGORY_HOURLY_MISSION:
        ser = EmployeeRequestHourlyMissionSerializer(data=cpy_data)
    elif category == EmployeeRequest.CATEGORY_DAILY_MISSION:
        ser = EmployeeRequestDailyMissionSerializer(data=cpy_data)
    elif category == EmployeeRequest.CATEGORY_OVERTIME:
        ser = EmployeeRequestOvertimeSerializer(data=cpy_data)
    elif category == EmployeeRequest.CATEGORY_HOURLY_SICK_LEAVE:
        ser = EmployeeRequestHourlySickLeaveSerializer(data=cpy_data)
    elif category == EmployeeRequest.CATEGORY_DAILY_SICK_LEAVE:
        ser = EmployeeRequestDailySickLeaveSerializer(data=cpy_data)
    elif category == EmployeeRequest.CATEGORY_HOURLY_UNPAID_LEAVE:
        ser = EmployeeRequestHourlyUnpaidLeaveSerializer(data=cpy_data)
    elif category == EmployeeRequest.CATEGORY_DAILY_UNPAID_LEAVE:
        ser = EmployeeRequestDailyUnpaidLeaveSerializer(data=cpy_data)
    elif category == EmployeeRequest.CATEGORY_PROJECT_MANUAL_TRAFFIC:
        ser = EmployeeRequestProjectManualTrafficSerializer(data=cpy_data)
    elif category == EmployeeRequest.CATEGORY_SHIFT_ROTATION:
        ser = EmployeeRequestShiftChangeSerializer(data=cpy_data)

    else:
        return Response({"msg": "category unaccepted"}, status=status.HTTP_400_BAD_REQUEST)
    if ser.is_valid():
        e = ser.save()
        return Response(EmployeeRequestOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
@check_user_permission(ADD_PERMISSION_STR, EmployeeRequest)
def create_employee_request(request, **kwargs):
    # cpy_data = request.data.copy()
    # cpy_data["employer"] = request.user.id
    # ser = EmployeeRequestSerializer(data=cpy_data)
    # if ser.is_valid():
    #     e = ser.save()
    #     return Response(EmployeeRequestOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    # return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    return manage_and_create_employee_request(kwargs)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, EmployeeRequest)
def update_employee_request_status(request, oid, **kwargs):
    r = get_object_or_404(EmployeeRequest, id=oid, employee__employer_id=kwargs["employer"])
    ser = EmployeeRequestSerializer(instance=r, data={"status": request.data.get("status")}, partial=True)
    if ser.is_valid():
        e = ser.save()
        return Response(EmployeeRequestOutputSerializer(e).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


def employee_requests_filter(kwargs, query=None):
    from_date = kwargs.get('from_date')
    to_date = kwargs.get('to_date')
    category = kwargs.get('category')
    employee = kwargs.get('employee_id')
    if not from_date and not to_date and not category and not employee:
        return Response({"msg": "invalid parameter"}, status=status.HTTP_400_BAD_REQUEST)
    result = query if query else EmployeeRequest.objects.filter(employer_id=kwargs["employer"])
    if from_date:
        result = result.filter(start_date__gte=from_date)
    if to_date:
        result = result.filter(end_date__lte=to_date)
    if category:
        result = result.filter(category=category)
    if employee:
        result = result.filter(employee_id=employee)
    return result


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, EmployeeRequest)
def search_employee_requests(request, **kwargs):
    result = employee_requests_filter(kwargs)
    ser = EmployeeRequestOutputSerializer(result, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, EmployeeRequest)
def get_employee_requests_excel(request, **kwargs):
    data_list = employee_requests_filter(kwargs)
    data = [["category", "employee", "start_date", "end_date", "registration_date", "action", ]]
    for fin in data_list:
        data.append([fin.category.name, fin.employee.get_full_name(), fin.start_date.strftime(DATE_FORMAT_STR), fin.end_date.strftime(DATE_FORMAT_STR),
                     fin.registration_date.strftime(DATE_FORMAT_STR), fin.get_action_display(), ])
    return send_response_file(data, 'employees')


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, EmployeeRequest)
def get_employees_requests_list(request, **kwargs):
    employees = Employee.objects.filter(employer_id=kwargs["employer"])
    requests_list = EmployeeRequest.objects.filter(employee_id__in=employees)
    ser = EmployeeRequestOutputSerializer(requests_list, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
@check_user_permission(ADD_PERMISSION_STR, WorkShift)
def create_work_shift(request, **kwargs):
    # cpy_data = request.data.copy()
    # cpy_data["employer"] = request.user.id
    ser = WorkShiftSerializer(data=kwargs)
    if ser.is_valid():
        e = ser.save()
        return Response(WorkShiftOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, WorkShift)
def search_work_shift(request, **kwargs):
    name = request.GET.get('name')
    if name is None:
        return Response({'error': '"name" is required'}, status=status.HTTP_400_BAD_REQUEST)
    employer = Employer.objects.get(id=kwargs["employer"])
    result = employer.workshift_set.objects.filter(name__icontains=name)
    ser = WorkShiftOutputSerializer(result, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([DELETE_METHOD_STR])
@check_user_permission(DELETE_PERMISSION_STR, WorkShift)
def delete_work_shift(request, oid, **kwargs):
    o = get_object_or_404(WorkShift, employer_id=kwargs["employer"], id=oid)
    o.delete()
    return Response({"msg": "DELETED"}, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, WorkShift)
def get_work_shifts_list(request, **kwargs):
    shifts = WorkShift.objects.filter(employer_id=kwargs["employer"])
    ser = WorkShiftOutputSerializer(shifts, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


# @api_view()
# def get_work_shift_plan_type_choices(request,  **kwargs):
#     return Response((WorkShiftPlan.PLAN_TYPE_CHOICES), status=status.HTTP_200_OK)

@api_view()
def get_employee_request_choices(request, **kwargs):
    return Response({
        "CATEGORY_CHOICES": EmployeeRequest.CATEGORY_CHOICES,
        "ACTION_CHOICES": EmployeeRequest.STATUS_CHOICES,
        "TRAFFIC_CHOICES": EmployeeRequest.TRAFFIC_CHOICES,
    }, status=status.HTTP_200_OK)


@api_view()
def get_employer_choices(request, **kwargs):
    return Response({
        "GENDER_CHOICES": Employer.GENDER_CHOICES,
        "PERSONALITY_CHOICES": Employer.PERSONALITY_CHOICES,
    }, status=status.HTTP_200_OK)


@api_view()
def get_attendance_device_choices(request, **kwargs):
    return Response({
        "STATUS_CHOICES": AttendanceDevice.STATUS_CHOICES,
    }, status=status.HTTP_200_OK)


@api_view()
def get_leave_policy_choices(request, **kwargs):
    return Response({
        "ACCEPTABLE_REGISTRATION_TYPE_CHOICES": LeavePolicy.ACCEPTABLE_REGISTRATION_TYPE_CHOICES,
    }, status=status.HTTP_200_OK)


@api_view()
def get_work_shift_plan_choices(request, **kwargs):
    return Response({
        "PLAN_TYPE_CHOICES": WorkShiftPlan.PLAN_TYPE_CHOICES,
    }, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
@check_user_permission(ADD_PERMISSION_STR, WorkShift)
def create_work_shift_plan(request, **kwargs):
    # cpy_data = request.data.copy()
    # is_many = False
    # if isinstance(request.data, list):
    #     is_many = True
    #     for item in cpy_data:
    #         item["employer"] = request.user.id
    # else:
    #     cpy_data["employer"] = request.user.id

    ser, is_many = handle_single_or_list_objects(request.data, kwargs["employer"], WorkShiftPlanSerializer)
    if ser.is_valid():
        e = ser.save()
        return Response(WorkShiftPlanOutputSerializer(e, many=is_many).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, WorkShift)
def update_work_shift_plan(request, **kwargs):
    cpy_data = request.data.copy()
    for item in cpy_data:
        item["employer"] = kwargs["employer"]
    work_shift_plans = get_list_or_404(WorkShiftPlan, employer_id=kwargs["employer"], work_shift_id=cpy_data[0]["work_shift"])
    ser = WorkShiftPlanUpdateSerializer(data=cpy_data, instance=work_shift_plans, many=True)
    if ser.is_valid():
        e = ser.save()
        return Response(WorkShiftPlanOutputSerializer(e, many=True).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, WorkShift)
def get_work_shift_plans_list(request, oid, **kwargs):
    shift = get_object_or_404(WorkShift, employer_id=kwargs["employer"], id=oid)
    ser = WorkShiftPlanOutputSerializer(shift.workshiftplan_set.all(), many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
@check_user_permission(ADD_PERMISSION_STR, Manager)
def create_manager(request, **kwargs):
    exp = datetime.strptime(request.data['expiration_date'], DATE_TIME_FORMAT_STR)
    if exp < now():
        return Response({"expiration_date": "تاریخ انقضای مسئولیت منقضی شده است"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    kwargs["employer_id"] = kwargs["employer"]
    ser = RegisterManagerSerializer(data=kwargs)
    if ser.is_valid():
        e = ser.save()
        perms = get_acceptable_permissions(filters=request.data.get("permissions")).values_list("id", flat=True)
        e.user_permissions.add(*perms)
        return Response(ManagerOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, Manager)
def update_manager(request, oid, **kwargs):
    exp = datetime.strptime(request.data['expiration_date'], DATE_TIME_FORMAT_STR)
    if exp < now():
        return Response({"expiration_date": "تاریخ انقضای مسئولیت منقضی شده است"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    mg = get_object_or_404(Manager, employer_id=kwargs["employer"], id=oid)
    ser = ManagerOutputSerializer(instance=mg, data=request.data, partial=True)
    if ser.is_valid():
        mg = ser.save()
    else:
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    if "permissions" in request.data:
        perms = get_acceptable_permissions(filters=request.data.get("permissions")).values_list("id", flat=True)
        mg.user_permissions.add(*perms)
    return Response(ManagerOutputSerializer(mg).data, status=status.HTTP_201_CREATED)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Manager)
def get_managers_list(request, **kwargs):
    mg = get_list_or_404(Manager, employer_id=kwargs["employer"])
    return Response(ManagerOutputSerializer(mg, many=True).data, status=status.HTTP_201_CREATED)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, Manager)
def get_manager(request, oid, **kwargs):
    mg = get_object_or_404(Manager, employer_id=kwargs["employer"], id=oid)
    return Response(ManagerOutputSerializer(mg).data, status=status.HTTP_201_CREATED)


@api_view([DELETE_METHOD_STR])
@check_user_permission(DELETE_PERMISSION_STR, Manager)
def delete_manager(request, oid, **kwargs):
    o = get_object_or_404(Manager, employer_id=kwargs["employer"], id=oid)
    o.delete()
    return Response({"msg": "DELETED"}, status=status.HTTP_200_OK)
