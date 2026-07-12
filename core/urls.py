from django.urls import path

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenBlacklistView,
)

from .views import CustomTokenObtainPairView


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
]