from rest_framework.permissions import BasePermission

from accounts.models import Employee


class IsAdmin(BasePermission):
    """
    Allows access only to Admin users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Employee.Role.ADMIN
        )


class IsAssetManager(BasePermission):
    """
    Allows access only to Asset Managers.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Employee.Role.ASSET_MANAGER
        )


class IsHOD(BasePermission):
    """
    Allows access only to Heads of Department.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Employee.Role.HOD
        )


class IsEmployee(BasePermission):
    """
    Allows access only to Employees.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Employee.Role.EMPLOYEE
        )


class IsAdminOrAssetManager(BasePermission):
    """
    Allows access to Admin or Asset Manager.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                Employee.Role.ADMIN,
                Employee.Role.ASSET_MANAGER,
            ]
        )


class IsAdminOrHOD(BasePermission):
    """
    Allows access to Admin or HOD.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                Employee.Role.ADMIN,
                Employee.Role.HOD,
            ]
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission.

    Admin can access every object.
    Employees can access only their own objects.
    """

    def has_object_permission(self, request, view, obj):

        if request.user.role == Employee.Role.ADMIN:
            return True

        if hasattr(obj, "employee"):
            return obj.employee == request.user

        if hasattr(obj, "reported_by"):
            return obj.reported_by == request.user

        if hasattr(obj, "requested_by"):
            return obj.requested_by == request.user

        return False