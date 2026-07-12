from django.urls import path
from .views import *

urlpatterns = [
    # Employee
    path("employees/", EmployeeListCreateView.as_view()),
    path("employees/<int:pk>/", EmployeeDetailView.as_view()),
    path("employees/<int:pk>/change-role/", ChangeEmployeeRoleView.as_view()),
    path("employees/<int:pk>/assign-department/", AssignDepartmentView.as_view()),
    path("employees/<int:pk>/activate/", ActivateEmployeeView.as_view()),
    path("employees/<int:pk>/deactivate/", DeactivateEmployeeView.as_view()),

    # Department
    path("departments/", DepartmentListCreateView.as_view()),
    path("departments/<int:pk>/", DepartmentDetailView.as_view()),
    path("departments/<int:pk>/assign-hod/", AssignHODView.as_view()),
    path("departments/<int:pk>/remove-hod/", RemoveHODView.as_view()),
    path("departments/<int:pk>/employees/", DepartmentEmployeesView.as_view()),
    path("departments/<int:pk>/assets/", DepartmentAssetsView.as_view()),
]