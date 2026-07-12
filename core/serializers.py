from rest_framework import serializers

from .models import Notification, ActivityLog

# Serializers convert JSON data into Django model and vice versa

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "title",
            "message",
            "is_read",
            "created_at",
        )
        read_only_fields = (
            "id",
            "title",
            "message",
            "created_at",
        )


class ActivityLogSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = (
            "id",
            "employee",
            "employee_name",
            "module",
            "action",
            "object_id",
            "timestamp",
            "ip_address",
        )
        read_only_fields = (
            "id",
            "timestamp",
        )

    def get_employee_name(self, obj):
        if obj.employee:
            return obj.employee.email
        return None

    
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["email"] = user.email
        token["role"] = user.role
        token["employee_id"] = user.employee_id

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data["employee"] = {
            "id": self.user.id,
            "employee_id": self.user.employee_id,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "role": self.user.role,
            "department": (
                self.user.department.name
                if self.user.department
                else None
            ),
        }

        return data