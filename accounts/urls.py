from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .authentication_views import LoginView, LogoutView
from .views import (
    EmployeeListCreateView,
    EmployeeDetailView,
    ChangeEmployeeRoleView,
    AssignDepartmentView,
    ActivateEmployeeView,
    DeactivateEmployeeView,
    DepartmentListCreateView,
    DepartmentDetailView,
    AssignHODView,
    RemoveHODView,
    DepartmentEmployeesView,
    DepartmentAssetsView,
)

urlpatterns = [
    # Authentication
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Employee
    path("employees/", EmployeeListCreateView.as_view(), name="employee-list"),
    path("employees/<int:pk>/", EmployeeDetailView.as_view(), name="employee-detail"),
    path("employees/<int:pk>/change-role/", ChangeEmployeeRoleView.as_view(), name="change-role"),
    path("employees/<int:pk>/assign-department/", AssignDepartmentView.as_view(), name="assign-department"),
    path("employees/<int:pk>/activate/", ActivateEmployeeView.as_view(), name="activate-employee"),
    path("employees/<int:pk>/deactivate/", DeactivateEmployeeView.as_view(), name="deactivate-employee"),

    # Department
    path("departments/", DepartmentListCreateView.as_view(), name="department-list"),
    path("departments/<int:pk>/", DepartmentDetailView.as_view(), name="department-detail"),
    path("departments/<int:pk>/assign-hod/", AssignHODView.as_view(), name="assign-hod"),
    path("departments/<int:pk>/remove-hod/", RemoveHODView.as_view(), name="remove-hod"),
    path("departments/<int:pk>/employees/", DepartmentEmployeesView.as_view(), name="department-employees"),
    path("departments/<int:pk>/assets/", DepartmentAssetsView.as_view(), name="department-assets"),
]