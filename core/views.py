from django.shortcuts import render

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