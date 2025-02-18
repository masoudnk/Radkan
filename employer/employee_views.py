from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from employer.models import Employee, EmployeeRequest, RollCall, RadkanMessage, RadkanMessageViewInfo
from employer.report_views import create_employee_total_report
from employer.serializers import EmployeeDashboardSerializer, RollCallSerializer, EmployeeRequestOutputSerializer, WorkShiftPlanOutputSerializer, RollCallOutputSerializer, \
    RadkanMessageSerializer, RollCallDepartureSerializer
from employer.views import manage_and_create_employee_request, POST_METHOD_STR


@api_view([POST_METHOD_STR])
def create_roll_call(request):
    cpy_data = request.data.copy()
    cpy_data["employee"] = request.user.id
    roll_calls = RollCall.objects.filter(employee_id=request.user.id, date=request.data['date'])
    if roll_calls.exists() and roll_calls.last().departure is None:
        ser = RollCallDepartureSerializer(data=request.data, instance=roll_calls.last(), partial=True)
    else:
        ser = RollCallSerializer(data=cpy_data, context={'request': request})
    if ser.is_valid(raise_exception=True):
        r = ser.save()
        return Response(RollCallOutputSerializer(r).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view()
def get_roll_calls_list(request, year, month):
    roll_calls = RollCall.objects.filter(employee_id=request.user.id, date__year=year, date__month=month)
    ser = RollCallOutputSerializer(roll_calls, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([POST_METHOD_STR])
def create_employee_request_for_employees(request):
    cpy_data = request.data.copy()
    cpy_data["employee_id"] = request.user.id
    return manage_and_create_employee_request(cpy_data)


@api_view([POST_METHOD_STR])
def get_message(request, oid):
    msg = RadkanMessage.objects.filter(employee_id=request.user.id, oid=oid)
    ser = RadkanMessageSerializer(msg)
    view_info = RadkanMessageViewInfo.objects.filter(employee_id=request.user.id, radkan_message_id=oid)
    if not view_info:
        RadkanMessageViewInfo.objects.create(employee_id=request.user.id, radkan_message_id=oid)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view()
def get_employee_requests_list(request, year, month):
    employee_requests = EmployeeRequest.objects.filter(employee_id=request.user.id)
    ser = EmployeeRequestOutputSerializer(employee_requests, many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view()
def get_employee_report_for_employees(request):
    employee = get_object_or_404(Employee, id=request.user.id)
    report = create_employee_total_report(employee,request.GET)
    return Response(report, status=status.HTTP_200_OK)


@api_view()
def get_employee_profile(request):
    employee = get_object_or_404(Employee, id=request.user.id)
    ser = EmployeeDashboardSerializer(employee)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view()
def get_employee_work_shift_plans_list(request):
    employee = get_object_or_404(Employee, id=request.user.id)
    ser = WorkShiftPlanOutputSerializer(employee.work_shift.workshiftplan_set.all(), many=True)
    return Response(ser.data, status=status.HTTP_200_OK)
