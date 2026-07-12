from django.urls import path

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenBlacklistView,
)
from .views import ReportAPIView
from .views import CustomTokenObtainPairView
from .views import DashboardAPIView

urlpatterns = [

    path(
        "login/",
        CustomTokenObtainPairView.as_view(),
        name="login",
    ),

    path(
        "refresh/",
        TokenRefreshView.as_view(),
        name="refresh",
    ),

    path(
        "logout/",
        TokenBlacklistView.as_view(),
        name="logout",
    ),

    path(
        "dashboard/",
        DashboardAPIView.as_view(),
        name="dashboard",
    ),

    path(
        "reports/<str:report_type>/",
        ReportAPIView.as_view(),
        name="reports",
    ),
]