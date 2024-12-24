import django.contrib.auth.password_validation as validators
from django.contrib.auth.hashers import make_password
from django.core import exceptions
from rest_framework import serializers

from employer.models import User, Employer, ResetPasswordRequest


class EmployerLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

class ResetPasswordRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResetPasswordRequest
        exclude = ()

class RegisterEmployerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    accepted_rules=serializers.BooleanField(write_only=True)

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
        fields = ("password","email", "username", "mobile","accepted_rules")
