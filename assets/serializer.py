from rest_framework import serializers

from accounts.models import Department
from assets.models import (
    Asset,
    AssetCategory,
    AssetAllocation,
    AssetTransfer,
    ResourceBooking,
    MaintenanceRequest,
)


# ============================================================
# Asset Category
# ============================================================

class AssetCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = AssetCategory
        fields = "__all__"


# ============================================================
# Asset Serializer (Read)
# ============================================================

class AssetSerializer(serializers.ModelSerializer):

    category = AssetCategorySerializer(read_only=True)

    department = serializers.StringRelatedField()

    class Meta:

        model = Asset

        fields = "__all__"

        read_only_fields = (
            "asset_code",
            "created_at",
            "updated_at",
        )


# ============================================================
# Asset Create Serializer
# ============================================================

class AssetCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = Asset

        exclude = (
            "asset_code",
            "created_at",
            "updated_at",
        )

    def validate_name(self, value):

        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Asset name must contain at least 3 characters."
            )

        return value

    def validate_purchase_cost(self, value):

        if value <= 0:

            raise serializers.ValidationError(
                "Purchase cost must be greater than zero."
            )

        return value

    def validate_serial_number(self, value):

        value = value.strip()

        if Asset.objects.filter(
            serial_number__iexact=value
        ).exists():

            raise serializers.ValidationError(
                "Serial number already exists."
            )

        return value


# ============================================================
# Asset Update Serializer
# ============================================================

class AssetUpdateSerializer(serializers.ModelSerializer):

    class Meta:

        model = Asset

        exclude = (
            "asset_code",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "asset_code",
        )

    def validate_purchase_cost(self, value):

        if value <= 0:

            raise serializers.ValidationError(
                "Purchase cost must be greater than zero."
            )

        return value

    def validate_serial_number(self, value):

        asset = self.instance

        if Asset.objects.filter(
            serial_number__iexact=value
        ).exclude(
            pk=asset.pk
        ).exists():

            raise serializers.ValidationError(
                "Serial number already exists."
            )

        return value
    # ============================================================
# Asset Allocation Serializer (Read)
# ============================================================

class AssetAllocationSerializer(serializers.ModelSerializer):

    asset = AssetSerializer(read_only=True)

    employee = serializers.StringRelatedField()

    department = serializers.StringRelatedField()

    allocated_by = serializers.StringRelatedField()

    class Meta:

        model = AssetAllocation

        fields = "__all__"

        read_only_fields = (
            "allocated_on",
        )


# ============================================================
# Allocation Create Serializer
# ============================================================

class AllocationCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = AssetAllocation

        fields = (
            "asset",
            "employee",
            "department",
            "allocated_by",
            "expected_return_date",
            "remarks",
        )

    def validate_remarks(self, value):

        value = value.strip()

        if len(value) > 1000:

            raise serializers.ValidationError(
                "Remarks cannot exceed 1000 characters."
            )

        return value


# ============================================================
# Asset Transfer Serializer (Read)
# ============================================================

class AssetTransferSerializer(serializers.ModelSerializer):

    asset = AssetSerializer(read_only=True)

    from_department = serializers.StringRelatedField()

    to_department = serializers.StringRelatedField()

    from_employee = serializers.StringRelatedField()

    to_employee = serializers.StringRelatedField()

    requested_by = serializers.StringRelatedField()

    approved_by = serializers.StringRelatedField()

    class Meta:

        model = AssetTransfer

        fields = "__all__"

        read_only_fields = (
            "request_date",
            "approved_date",
            "completed_date",
        )


# ============================================================
# Transfer Request Serializer
# ============================================================

class TransferRequestSerializer(serializers.ModelSerializer):

    class Meta:

        model = AssetTransfer

        fields = (
            "asset",
            "to_department",
            "to_employee",
            "reason",
        )

    def validate_reason(self, value):

        value = value.strip()

        if len(value) < 10:

            raise serializers.ValidationError(
                "Reason must contain at least 10 characters."
            )

        if len(value) > 1000:

            raise serializers.ValidationError(
                "Reason cannot exceed 1000 characters."
            )

        return value
    # ============================================================
# Resource Booking Serializer (Read)
# ============================================================

class ResourceBookingSerializer(serializers.ModelSerializer):

    asset = AssetSerializer(read_only=True)

    employee = serializers.StringRelatedField()

    class Meta:

        model = ResourceBooking

        fields = "__all__"

        read_only_fields = (
            "created_at",
        )


# ============================================================
# Booking Create Serializer
# ============================================================

class BookingCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = ResourceBooking

        fields = (
            "asset",
            "employee",
            "purpose",
            "start_datetime",
            "end_datetime",
        )

    def validate_purpose(self, value):

        value = value.strip()

        if len(value) < 5:

            raise serializers.ValidationError(
                "Purpose must contain at least 5 characters."
            )

        return value

    def validate(self, attrs):

        if attrs["start_datetime"] >= attrs["end_datetime"]:

            raise serializers.ValidationError(
                "End time must be greater than start time."
            )

        return attrs


# ============================================================
# Maintenance Request Serializer (Read)
# ============================================================

class MaintenanceRequestSerializer(serializers.ModelSerializer):

    asset = AssetSerializer(read_only=True)

    reported_by = serializers.StringRelatedField()

    assigned_to = serializers.StringRelatedField()

    class Meta:

        model = MaintenanceRequest

        fields = "__all__"

        read_only_fields = (
            "reported_on",
            "resolved_on",
        )


# ============================================================
# Maintenance Create Serializer
# ============================================================

class MaintenanceCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = MaintenanceRequest

        fields = (
            "asset",
            "issue",
            "priority",
        )

    def validate_issue(self, value):

        value = value.strip()

        if len(value) < 10:

            raise serializers.ValidationError(
                "Issue description is too short."
            )

        return value