from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from employer.views import POST_METHOD_STR, DELETE_METHOD_STR
from .serializers import *

@api_view([POST_METHOD_STR])
def create_work_policy(request):
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    ser=WorkPolicySerializer(data=cpy_data)
    if ser.is_valid():
        e=ser.save()
        return Response(WorkPolicyOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view([DELETE_METHOD_STR])
def delete_work_policy(request, oid):
    o = get_object_or_404(WorkPolicy, employer_id=request.user.id, id=oid)
    o.delete()
    return Response({"msg": "DELETED"}, status=status.HTTP_200_OK)

# todo create update method for WorkPolicy and change this creating style

# todo create get_work_policy_by_id

@api_view([POST_METHOD_STR])
def create_earned_leave_policy(request):
    wp=get_object_or_404(WorkPolicy, id=request.POST.get('work_policy_id'),employer_id=request.user.id)
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    cpy_data["work_policy"] = wp.id
    ser=EarnedLeavePolicySerializer(data=cpy_data)
    if ser.is_valid():
        e=ser.save()
        return Response(EarnedLeavePolicyOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
def create_sick_leave_policy(request):
    wp=get_object_or_404(WorkPolicy, id=request.POST.get('work_policy_id'),employer_id=request.user.id)
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    cpy_data["work_policy"] = wp.id
    ser=SickLeavePolicySerializer(data=cpy_data)
    if ser.is_valid():
        e=ser.save()
        return Response(SickLeavePolicyOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view([POST_METHOD_STR])
def create_overtime_policy(request):
    wp=get_object_or_404(WorkPolicy, id=request.POST.get('work_policy_id'),employer_id=request.user.id)
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    cpy_data["work_policy"] = wp.id
    ser=OvertimePolicySerializer(data=cpy_data)
    if ser.is_valid():
        e=ser.save()
        return Response(OvertimePolicyOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
def create_manual_traffic_policy(request):
    wp=get_object_or_404(WorkPolicy, id=request.POST.get('work_policy_id'),employer_id=request.user.id)
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    cpy_data["work_policy"] = wp.id
    ser=ManualTrafficPolicySerializer(data=cpy_data)
    if ser.is_valid():
        e=ser.save()
        return Response(ManualTrafficPolicyOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
def create_work_mission_policy(request):
    wp=get_object_or_404(WorkPolicy, id=request.POST.get('work_policy_id'),employer_id=request.user.id)
    cpy_data = request.data.copy()
    cpy_data["employer"] = request.user.id
    cpy_data["work_policy"] = wp.id
    ser=WorkMissionPolicySerializer(data=cpy_data)
    if ser.is_valid():
        e=ser.save()
        return Response(WorkMissionPolicyOutputSerializer(e).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

