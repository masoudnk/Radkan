from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from employer.views import POST_METHOD_STR

from .serializers import *

class Home(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user.username
        content = {'message': user}
        return Response(content)

