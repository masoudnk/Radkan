from datetime import timedelta

from django.contrib.auth.forms import UsernameField
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import authentication_classes, permission_classes, api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from employer.forms import EmployerForm
from employer.models import User
from employer.serializers import RegisterEmployerSerializer, EmployerLoginSerializer, ResetPasswordRequestSerializer

POST_METHOD_STR="POST"
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
    email_or_mobile = request.POST.get('email_or_mobile')
    # todo think about how council such sensitive information
    #  user=get_object_or_404(User,(Q(email=email_or_mobile)|Q(mobile=email_or_mobile)))
    # user=get_object_or_404(User,(Q(email=email_or_mobile)|Q(mobile=email_or_mobile)))
    user=get_object_or_404(User,username=request.POST.get('username'))
    request_list=user.resetpasswordrequest_set.filter(active=True,request_date__gte=now() -timedelta(hours=1))
    if request_list.exists():
        active_request=request_list.filter(code=request.POST.get('code'))
        if active_request.exists():
            if len(active_request)==1:
                active_request[0].active=False
                active_request[0].save()
                return Response({"msg":"password changed"}, status=status.HTTP_200_OK)

    return Response({"msg":"multiple or unacceptable requests"},status=status.HTTP_400_BAD_REQUEST)


@api_view([POST_METHOD_STR])
@authentication_classes([])
@permission_classes([])
def create_password_reset_request(request):
    print(request.POST)
    mobile=request.POST.get('mobile')
    #todo think about how council such sensitive information
    # user=get_object_or_404(User,(Q(email=email_or_mobile)|Q(mobile=email_or_mobile)))
    user=get_object_or_404(User,username=request.POST.get('username'))
    ser=ResetPasswordRequestSerializer(data={"user":user.id})
    if ser.is_valid():
        ser.save()
        #todo send sms to user
        return Response({"msg":"created"}, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


# class RegisterEmployer(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         ser=RegisterEmployerSerializer(data=request.data)
#         if ser.is_valid():
#             ser.save()
#             return Response(ser.data, status=status.HTTP_200_OK)
#
#         else:
#             return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view([POST_METHOD_STR])
def register_employer(request):
        ser=RegisterEmployerSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_200_OK)

        else:
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


