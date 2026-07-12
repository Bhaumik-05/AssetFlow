from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from core.views_html import (
    login_view,
    logout_view,
    dashboard_view,
    employees_view,
    departments_view,
    assets_view,
    categories_view,
    allocations_view,
    transfers_view,
    maintenance_view,
    bookings_view,
    audit_cycles_view,
    audit_records_view,
    notifications_view,
    activity_logs_view,
    reports_view,
)

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="login_view", permanent=False)),
    path("admin/", admin.site.urls),
    path("app/login/", login_view, name="login_view"),
    path("app/logout/", logout_view, name="logout_view"),
    path("app/dashboard/", dashboard_view, name="dashboard"),
    path("app/employees/", employees_view, name="employees"),
    path("app/departments/", departments_view, name="departments"),
    path("app/assets/", assets_view, name="assets"),
    path("app/categories/", categories_view, name="categories"),
    path("app/allocations/", allocations_view, name="allocations"),
    path("app/transfers/", transfers_view, name="transfers"),
    path("app/maintenance/", maintenance_view, name="maintenance"),
    path("app/bookings/", bookings_view, name="bookings"),
    path("app/audit-cycles/", audit_cycles_view, name="audit_cycles"),
    path("app/audit-records/", audit_records_view, name="audit_records"),
    path("app/notifications/", notifications_view, name="notifications"),
    path("app/activity-logs/", activity_logs_view, name="activity_logs"),
    path("app/reports/", reports_view, name="reports"),

    path("api/", include("accounts.urls")),
    path("api/audits/", include("audits.urls")),
    path("api/auth/", include("core.urls")),
]
