from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/", include("accounts.urls")),
    path("api/audits/", include("audits.urls")),
    path("api/auth/",include("core.urls"),),
]