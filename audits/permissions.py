from rest_framework.permissions import BasePermission

from accounts.models import Employee


class IsAuditManager(BasePermission):
    """
    Allows only Admins and Asset Managers.
    """

    message = "Only Admin or Asset Manager can perform this action."

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        return user.role in (
            Employee.Role.ADMIN,
            Employee.Role.ASSET_MANAGER,
        )


class IsAuditViewer(BasePermission):
    """
    Allows Admins, Asset Managers and HODs
    to view audit information.
    """

    message = "You do not have permission to view audits."

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        return user.role in (
            Employee.Role.ADMIN,
            Employee.Role.ASSET_MANAGER,
            Employee.Role.HOD,
        )