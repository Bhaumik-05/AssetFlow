from rest_framework import serializers

from .models import AuditCycle, AuditRecord


class AuditCycleSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source="department.name",
        read_only=True
    )

    conducted_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditCycle
        fields = (
            "id",
            "title",
            "department",
            "department_name",
            "start_date",
            "end_date",
            "conducted_by",
            "conducted_by_name",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "created_at",
            "updated_at",
        )

    def get_conducted_by_name(self, obj):
        if obj.conducted_by:
            return obj.conducted_by.email
        return None


class AuditRecordSerializer(serializers.ModelSerializer):
    asset_code = serializers.CharField(
        source="asset.asset_code",
        read_only=True
    )

    asset_name = serializers.CharField(
        source="asset.name",
        read_only=True
    )

    verified_by_name = serializers.SerializerMethodField()

    audit_title = serializers.CharField(
        source="audit_cycle.title",
        read_only=True
    )

    class Meta:
        model = AuditRecord
        fields = (
            "id",
            "audit_cycle",
            "audit_title",
            "asset",
            "asset_code",
            "asset_name",
            "verified_by",
            "verified_by_name",
            "condition",
            "status",
            "remarks",
            "is_verified",
            "verified_on",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "verified_on",
            "created_at",
            "updated_at",
        )

    def get_verified_by_name(self, obj):
        if obj.verified_by:
            return obj.verified_by.email
        return None