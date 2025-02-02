from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from employer.views import POST_METHOD_STR, DELETE_METHOD_STR, check_user_permission
from .serializers import *
from .utilities import PUT_METHOD_STR, CHANGE_PERMISSION_STR, ADD_PERMISSION_STR, DELETE_PERMISSION_STR, VIEW_PERMISSION_STR


@api_view([POST_METHOD_STR])
@check_user_permission(ADD_PERMISSION_STR, WorkPolicy)
def create_work_policy(request, **kwargs):
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    ser = WorkPolicySerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(WorkPolicyOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([DELETE_METHOD_STR])
@check_user_permission(DELETE_PERMISSION_STR, WorkPolicy)
def delete_work_policy(request, oid, **kwargs):
    o = get_object_or_404(WorkPolicy, employer_id=request.user.id, id=oid)
    o.delete()
    return Response({"msg": "DELETED"}, status=status.HTTP_200_OK)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, WorkPolicy)
def update_work_policy(request, oid, **kwargs):
    wp = get_object_or_404(WorkPolicy, employer_id=kwargs["employer"], id=oid)
    # using output serializer to prevent change employer
    ser = WorkPolicyOutputSerializer(data=request.data, instance=wp, partial=True)
    if ser.is_valid():
        w = ser.save()
        return Response(WorkPolicyFullDetailsOutputSerializer(instance=w).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view()
def get_leave_policy_choices(request, **kwargs):
    return Response({
        "ACCEPTABLE_REGISTRATION_TYPE_CHOICES": LeavePolicy.ACCEPTABLE_REGISTRATION_TYPE_CHOICES,
    }, status=status.HTTP_200_OK)

@api_view()
def get_work_policy(request, oid, **kwargs):
    wp = get_object_or_404(WorkPolicy, employer_id=request.user.id, id=oid)
    ser = WorkPolicyFullDetailsOutputSerializer(instance=wp)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view()
@check_user_permission(VIEW_PERMISSION_STR, WorkPolicy)
def get_work_policies_list(request,  **kwargs):
    wp = WorkPolicy.objects.filter(employer_id=kwargs['employer'])
    ser = WorkPolicyFullDetailsOutputSerializer(instance=wp,many=True)
    return Response(ser.data, status=status.HTTP_200_OK)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, EarnedLeavePolicy)
def update_earned_leave_policy(request, wp_id, **kwargs):
    wp = get_object_or_404(WorkPolicy, employer_id=request.user.id, id=wp_id)
    ser = EarnedLeavePolicyUpdateSerializer(data=request.data, instance=wp.earnedleavepolicy, partial=True)
    if ser.is_valid(raise_exception=True):
        obj = ser.save()
        return Response(EarnedLeavePolicyOutputSerializer(obj).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, SickLeavePolicy)
def update_sick_leave_policy(request, wp_id, **kwargs):
    wp = get_object_or_404(WorkPolicy, employer_id=request.user.id, id=wp_id)
    ser = SickLeavePolicyUpdateSerializer(data=request.data, instance=wp.sickleavepolicy, partial=True)
    if ser.is_valid(raise_exception=True):
        obj = ser.save()
        return Response(SickLeavePolicyOutputSerializer(obj).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, OvertimePolicy)
def update_overtime_policy(request, wp_id, **kwargs):
    wp = get_object_or_404(WorkPolicy, employer_id=request.user.id, id=wp_id)
    ser = OvertimePolicyUpdateSerializer(data=request.data, instance=wp.overtimepolicy, partial=True)
    if ser.is_valid(raise_exception=True):
        obj = ser.save()
        return Response(OvertimePolicyOutputSerializer(obj).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, ManualTrafficPolicy)
def update_manual_traffic_policy(request, wp_id, **kwargs):
    wp = get_object_or_404(WorkPolicy, employer_id=request.user.id, id=wp_id)
    ser = ManualTrafficPolicyUpdateSerializer(data=request.data, instance=wp.manualtrafficpolicy, partial=True)
    if ser.is_valid(raise_exception=True):
        obj = ser.save()
        return Response(ManualTrafficPolicyOutputSerializer(obj).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([PUT_METHOD_STR])
@check_user_permission(CHANGE_PERMISSION_STR, WorkMissionPolicy)
def update_work_mission_policy(request, wp_id, **kwargs):
    wp = get_object_or_404(WorkPolicy, employer_id=request.user.id, id=wp_id)
    ser = WorkMissionPolicyUpdateSerializer(data=request.data, instance=wp.workmissionpolicy, partial=True)
    if ser.is_valid(raise_exception=True):
        obj = ser.save()
        return Response(WorkMissionPolicyOutputSerializer(obj).data, status=status.HTTP_200_OK)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
def create_earned_leave_policy(request, **kwargs):
    print(request.data)
    wp = get_object_or_404(WorkPolicy, id=request.data.get('work_policy_id'), employer_id=request.user.id)
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    cpy_data["work_policy"] = wp.id
    ser = EarnedLeavePolicySerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(EarnedLeavePolicyOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
def create_sick_leave_policy(request, **kwargs):
    wp = get_object_or_404(WorkPolicy, id=request.data.get('work_policy_id'), employer_id=request.user.id)
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    cpy_data["work_policy"] = wp.id
    ser = SickLeavePolicySerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(SickLeavePolicyOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
def create_overtime_policy(request, **kwargs):
    wp = get_object_or_404(WorkPolicy, id=request.data.get('work_policy_id'), employer_id=request.user.id)
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    cpy_data["work_policy"] = wp.id
    ser = OvertimePolicySerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(OvertimePolicyOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
def create_manual_traffic_policy(request, **kwargs):
    wp = get_object_or_404(WorkPolicy, id=request.data.get('work_policy_id'), employer_id=request.user.id)
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    cpy_data["work_policy"] = wp.id
    ser = ManualTrafficPolicySerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(ManualTrafficPolicyOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
def create_work_mission_policy(request, **kwargs):
    wp = get_object_or_404(WorkPolicy, id=request.data.get('work_policy_id'), employer_id=request.user.id)
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    cpy_data["work_policy"] = wp.id
    ser = WorkMissionPolicySerializer(data=cpy_data)
    if ser.is_valid():
        e = ser.save()
        return Response(WorkMissionPolicyOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
