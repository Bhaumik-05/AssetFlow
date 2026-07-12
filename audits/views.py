from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AuditCycle, AuditRecord
from .permissions import (
    IsAuditManager,
    IsAuditViewer,
)
from .serializers import (
    AuditCycleSerializer,
    AuditRecordSerializer,
)
from .service import AuditService


class AuditCycleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    API endpoints for Audit Cycles.
    """

    serializer_class = AuditCycleSerializer

    queryset = (
        AuditCycle.objects
        .select_related(
            "department",
            "conducted_by",
        )
        .order_by("-start_date")
    )

    def get_permissions(self):
        """
        Role Based Permissions

        View Audit      -> Admin, Asset Manager, HOD
        Create Audit    -> Admin, Asset Manager
        Start Audit     -> Admin, Asset Manager
        Complete Audit  -> Admin, Asset Manager
        Report          -> Admin, Asset Manager, HOD
        """

        if self.action in [
            "list",
            "retrieve",
            "report",
        ]:
            permission_classes = [IsAuditViewer]
        else:
            permission_classes = [IsAuditManager]

        return [
            permission()
            for permission in permission_classes
        ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        audit_cycle = AuditService.create_audit_cycle(
            title=serializer.validated_data["title"],
            department=serializer.validated_data["department"],
            start_date=serializer.validated_data["start_date"],
            end_date=serializer.validated_data["end_date"],
            conducted_by=serializer.validated_data["conducted_by"],
        )

        output = self.get_serializer(audit_cycle)

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        audit_cycle = self.get_object()

        result = AuditService.start_audit(
            audit_cycle
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def identify_missing(self, request, pk=None):
        audit_cycle = self.get_object()

        result = AuditService.identify_missing_assets(
            audit_cycle
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        audit_cycle = self.get_object()

        result = AuditService.complete_audit(
            audit_cycle
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def report(self, request, pk=None):
        audit_cycle = self.get_object()

        report = AuditService.generate_audit_report(
            audit_cycle
        )

        return Response(
            report,
            status=status.HTTP_200_OK,
        )


class AuditRecordViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    API endpoints for Audit Records.
    """

    serializer_class = AuditRecordSerializer

    queryset = (
        AuditRecord.objects
        .select_related(
            "audit_cycle",
            "asset",
            "verified_by",
        )
        .order_by("-verified_on")
    )

    def get_permissions(self):
        """
        Role Based Permissions

        View Records   -> Admin, Asset Manager, HOD
        Verify Asset   -> Admin, Asset Manager
        """

        if self.action in [
            "list",
            "retrieve",
        ]:
            permission_classes = [IsAuditViewer]
        else:
            permission_classes = [IsAuditManager]

        return [
            permission()
            for permission in permission_classes
        ]

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        audit_record = self.get_object()

        result = AuditService.verify_asset(
            audit_record=audit_record,
            verified_by=request.user,
            condition=request.data.get("condition"),
            status=request.data.get("status"),
            remarks=request.data.get("remarks", ""),
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )