from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Employee
from assets.models import (
    Asset,
    AssetAllocation,
    AssetCategory,
    AssetTransfer,
    MaintenanceRequest,
    ResourceBooking,
)
from assets.serializer import (
    AllocationCreateSerializer,
    AssetAllocationSerializer,
    AssetCategorySerializer,
    AssetCreateSerializer,
    AssetSerializer,
    AssetTransferSerializer,
    AssetUpdateSerializer,
    BookingCreateSerializer,
    MaintenanceCreateSerializer,
    MaintenanceRequestSerializer,
    ResourceBookingSerializer,
    TransferRequestSerializer,
)
from assets.service import (
    AllocationService,
    AssetService,
    BookingService,
    MaintenanceService,
    TransferService,
)


class BaseAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def success(self, message, data=None, status_code=status.HTTP_200_OK):
        return Response(
            {
                "success": True,
                "message": message,
                "data": data,
            },
            status=status_code,
        )

    def error(self, message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        return Response(
            {
                "success": False,
                "message": message,
                "errors": errors,
            },
            status=status_code,
        )

    def execute(self, callback):
        try:
            return callback()
        except ValidationError as exc:
            return self.error(
                message="Validation failed.",
                errors=getattr(exc, "message_dict", str(exc)),
            )
        except Exception as exc:
            return self.error(
                message="Internal server error.",
                errors=str(exc),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_instance(self, model, pk, queryset=None):
        queryset = queryset or model.objects.all()
        return get_object_or_404(queryset, pk=pk)


class AssetCategoryAPIView(BaseAPIView):
    serializer_class = AssetCategorySerializer

    def get(self, request):
        queryset = AssetCategory.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return self.success("Categories fetched successfully.", serializer.data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return self.success(
            "Category created successfully.",
            AssetCategorySerializer(category).data,
            status.HTTP_201_CREATED,
        )


class AssetAPIView(BaseAPIView):
    def get(self, request, pk=None):
        queryset = Asset.objects.select_related("category", "department")

        if pk:
            asset = self.get_instance(Asset, pk, queryset)
            serializer = AssetSerializer(asset)
            return self.success("Asset fetched successfully.", serializer.data)

        serializer = AssetSerializer(queryset, many=True)
        return self.success("Assets fetched successfully.", serializer.data)

    def post(self, request):
        serializer = AssetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def operation():
            asset = AssetService.create_asset(**serializer.validated_data)
            return self.success(
                "Asset created successfully.",
                AssetSerializer(asset).data,
                status.HTTP_201_CREATED,
            )

        return self.execute(operation)

    def put(self, request, pk):
        asset = self.get_instance(Asset, pk)
        serializer = AssetUpdateSerializer(asset, data=request.data)
        serializer.is_valid(raise_exception=True)

        def operation():
            updated_asset = AssetService.update_asset(asset=asset, **serializer.validated_data)
            return self.success(
                "Asset updated successfully.",
                AssetSerializer(updated_asset).data,
            )

        return self.execute(operation)

    def delete(self, request, pk):
        asset = self.get_instance(Asset, pk)
        asset.delete()
        return self.success("Asset deleted successfully.")


class AllocationAPIView(BaseAPIView):
    def get(self, request, pk=None):
        queryset = (
            AssetAllocation.objects.select_related(
                "asset",
                "employee",
                "department",
                "allocated_by",
            ).order_by("-allocated_on")
        )

        if pk:
            allocation = self.get_instance(AssetAllocation, pk, queryset)
            serializer = AssetAllocationSerializer(allocation)
            return self.success("Allocation fetched successfully.", serializer.data)

        serializer = AssetAllocationSerializer(queryset, many=True)
        return self.success("Allocation history fetched successfully.", serializer.data)

    def post(self, request):
        serializer = AllocationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def operation():
            allocation = AllocationService.allocate_asset(**serializer.validated_data)
            return self.success(
                "Asset allocated successfully.",
                AssetAllocationSerializer(allocation).data,
                status.HTTP_201_CREATED,
            )

        return self.execute(operation)

    def put(self, request, pk):
        allocation = self.get_instance(AssetAllocation, pk)

        def operation():
            AllocationService.return_asset(
                asset=allocation.asset,
                returned_on=request.data.get("returned_on"),
                remarks=request.data.get("remarks", ""),
            )
            allocation.refresh_from_db()
            return self.success(
                "Asset returned successfully.",
                AssetAllocationSerializer(allocation).data,
            )

        return self.execute(operation)

    def delete(self, request, pk):
        allocation = self.get_instance(AssetAllocation, pk)

        def operation():
            AllocationService.cancel_allocation(
                allocation=allocation,
                remarks=request.data.get("remarks", ""),
            )
            allocation.refresh_from_db()
            return self.success(
                "Allocation cancelled successfully.",
                AssetAllocationSerializer(allocation).data,
            )

        return self.execute(operation)


class TransferAPIView(BaseAPIView):
    def get(self, request, pk=None):
        queryset = (
            AssetTransfer.objects.select_related(
                "asset",
                "from_department",
                "to_department",
                "from_employee",
                "to_employee",
                "requested_by",
                "approved_by",
            ).order_by("-request_date")
        )

        if pk:
            transfer = self.get_instance(AssetTransfer, pk, queryset)
            serializer = AssetTransferSerializer(transfer)
            return self.success("Transfer fetched successfully.", serializer.data)

        serializer = AssetTransferSerializer(queryset, many=True)
        return self.success("Transfer history fetched successfully.", serializer.data)

    def post(self, request):
        serializer = TransferRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def operation():
            transfer = TransferService.request_transfer(requested_by=request.user, **serializer.validated_data)
            return self.success(
                "Transfer request created successfully.",
                AssetTransferSerializer(transfer).data,
                status.HTTP_201_CREATED,
            )

        return self.execute(operation)

    def put(self, request, pk):
        transfer = self.get_instance(AssetTransfer, pk)

        def operation():
            TransferService.approve_transfer(transfer=transfer, approved_by=request.user)
            transfer.refresh_from_db()
            return self.success(
                "Transfer approved successfully.",
                AssetTransferSerializer(transfer).data,
            )

        return self.execute(operation)

    def patch(self, request, pk):
        transfer = self.get_instance(AssetTransfer, pk)

        def operation():
            TransferService.reject_transfer(
                transfer=transfer,
                approved_by=request.user,
                reason=request.data.get("reason", ""),
            )
            transfer.refresh_from_db()
            return self.success(
                "Transfer rejected successfully.",
                AssetTransferSerializer(transfer).data,
            )

        return self.execute(operation)

    def delete(self, request, pk):
        transfer = self.get_instance(AssetTransfer, pk)

        def operation():
            allocation = TransferService.complete_transfer(transfer=transfer)
            transfer.refresh_from_db()
            return self.success(
                "Transfer completed successfully.",
                {
                    "transfer": AssetTransferSerializer(transfer).data,
                    "allocation": AssetAllocationSerializer(allocation).data,
                },
            )

        return self.execute(operation)


class BookingAPIView(BaseAPIView):
    def get(self, request, pk=None):
        queryset = ResourceBooking.objects.select_related("asset", "employee").order_by("-created_at")

        if pk:
            booking = self.get_instance(ResourceBooking, pk, queryset)
            serializer = ResourceBookingSerializer(booking)
            return self.success("Booking fetched successfully.", serializer.data)

        serializer = ResourceBookingSerializer(queryset, many=True)
        return self.success("Bookings fetched successfully.", serializer.data)

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def operation():
            booking = BookingService.create_booking(**serializer.validated_data)
            return self.success(
                "Booking created successfully.",
                ResourceBookingSerializer(booking).data,
                status.HTTP_201_CREATED,
            )

        return self.execute(operation)

    def put(self, request, pk):
        booking = self.get_instance(ResourceBooking, pk)

        def operation():
            BookingService.approve_booking(booking=booking, approved_by=request.user)
            booking.refresh_from_db()
            return self.success(
                "Booking approved successfully.",
                ResourceBookingSerializer(booking).data,
            )

        return self.execute(operation)

    def patch(self, request, pk):
        booking = self.get_instance(ResourceBooking, pk)

        def operation():
            BookingService.cancel_booking(
                booking=booking,
                cancelled_by=request.user,
                reason=request.data.get("reason", ""),
            )
            booking.refresh_from_db()
            return self.success(
                "Booking cancelled successfully.",
                ResourceBookingSerializer(booking).data,
            )

        return self.execute(operation)

    def delete(self, request, pk):
        booking = self.get_instance(ResourceBooking, pk)

        def operation():
            BookingService.complete_booking(booking=booking)
            booking.refresh_from_db()
            return self.success(
                "Booking completed successfully.",
                ResourceBookingSerializer(booking).data,
            )

        return self.execute(operation)


class MaintenanceAPIView(BaseAPIView):
    def get(self, request, pk=None):
        queryset = (
            MaintenanceRequest.objects.select_related("asset", "reported_by", "assigned_to").order_by("-reported_on")
        )

        if pk:
            maintenance = self.get_instance(MaintenanceRequest, pk, queryset)
            serializer = MaintenanceRequestSerializer(maintenance)
            return self.success("Maintenance request fetched successfully.", serializer.data)

        serializer = MaintenanceRequestSerializer(queryset, many=True)
        return self.success("Maintenance requests fetched successfully.", serializer.data)

    def post(self, request):
        serializer = MaintenanceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def operation():
            maintenance = MaintenanceService.create_request(reported_by=request.user, **serializer.validated_data)
            return self.success(
                "Maintenance request created successfully.",
                MaintenanceRequestSerializer(maintenance).data,
                status.HTTP_201_CREATED,
            )

        return self.execute(operation)

    def put(self, request, pk):
        maintenance = self.get_instance(MaintenanceRequest, pk)

        def operation():
            MaintenanceService.approve_request(request=maintenance, approved_by=request.user)
            maintenance.refresh_from_db()
            return self.success(
                "Maintenance request approved successfully.",
                MaintenanceRequestSerializer(maintenance).data,
            )

        return self.execute(operation)

    def patch(self, request, pk):
        maintenance = self.get_instance(MaintenanceRequest, pk)
        employee = self.get_instance(Employee, request.data.get("employee_id"))

        def operation():
            MaintenanceService.assign_employee(request=maintenance, employee=employee)
            maintenance.refresh_from_db()
            return self.success(
                "Maintenance assigned successfully.",
                MaintenanceRequestSerializer(maintenance).data,
            )

        return self.execute(operation)

    def delete(self, request, pk):
        maintenance = self.get_instance(MaintenanceRequest, pk)

        def operation():
            MaintenanceService.resolve_request(request=maintenance, remarks=request.data.get("remarks", ""))
            maintenance.refresh_from_db()
            return self.success(
                "Maintenance resolved successfully.",
                MaintenanceRequestSerializer(maintenance).data,
            )

        return self.execute(operation)
