from django.shortcuts import render
from .report_service import ReportService
# Create your views here.
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification, ActivityLog
from .serializers import (
    NotificationSerializer,
    ActivityLogSerializer,
)
from .service import mark_notification_as_read


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Notification.objects
            .filter(employee=self.request.user)
            .order_by("-created_at")
        )

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()

        mark_notification_as_read(notification)

        serializer = self.get_serializer(notification)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        self.get_queryset().filter(
            is_read=False
        ).update(is_read=True)

        return Response(
            {"detail": "All notifications marked as read."},
            status=status.HTTP_200_OK,
        )

from .permissions import IsAdmin

class ActivityLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAdmin]

    queryset = (
        ActivityLog.objects
        .select_related("employee")
        .order_by("-timestamp")
    )
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

from rest_framework.views import APIView

from .dashboard_service import DashboardService

class DashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        if user.role == user.Role.ADMIN:

            data = DashboardService.admin_dashboard()

        elif user.role == user.Role.ASSET_MANAGER:

            data = DashboardService.asset_manager_dashboard()

        elif user.role == user.Role.HOD:

            data = DashboardService.hod_dashboard(user)

        else:

            data = DashboardService.employee_dashboard(user)

        return Response(data)

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .permissions import IsAdminOrAssetManager
from .report_service import ReportService


class ReportAPIView(APIView):
    """
    APIs for system reports.

    GET /reports/assets/
    GET /reports/departments/
    GET /reports/maintenance/
    GET /reports/bookings/
    GET /reports/transfers/
    GET /reports/audits/
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminOrAssetManager
    ]

    def get(self, request, report_type):

        reports = {

            "assets":
                ReportService.asset_utilization,

            "departments":
                ReportService.department_asset_report,

            "maintenance":
                ReportService.maintenance_statistics,

            "bookings":
                ReportService.booking_statistics,

            "transfers":
                ReportService.transfer_statistics,

            "audits":
                ReportService.audit_statistics,
        }

        report = reports.get(report_type)

        if report is None:

            return Response(
                {
                    "error": "Invalid report type."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            report(),
            status=status.HTTP_200_OK
        )