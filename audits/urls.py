from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuditCycleViewSet,
    AuditRecordViewSet,
)

router = DefaultRouter()

router.register(
    r"cycles",
    AuditCycleViewSet,
    basename="audit-cycle",
)

router.register(
    r"records",
    AuditRecordViewSet,
    basename="audit-record",
)

urlpatterns = [
    path("", include(router.urls)),
]