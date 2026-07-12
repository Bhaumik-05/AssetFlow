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