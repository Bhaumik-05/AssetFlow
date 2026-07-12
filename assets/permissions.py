from accounts.models import Employee

from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    """
    Base permission class for all Asset module permissions.
    Every permission class should inherit from this class.
    """

    message = "You do not have permission to perform this action."

    # ==========================================================
    # Common Authentication Check
    # ==========================================================

    def has_permission(self, request, view):

        user = request.user

        return (
            user.is_authenticated
            and user.is_active
            and self.check_permission(request)
        )

    # ==========================================================
    # Override in Child Classes
    # ==========================================================

    def check_permission(self, request):
        """
        Override this method in subclasses.
        """

        return False

    # ==========================================================
    # Helper Methods
    # ==========================================================

    @staticmethod
    def is_admin(user):

        return user.role == Employee.Role.ADMIN

    @staticmethod
    def is_asset_manager(user):

        return user.role == Employee.Role.ASSET_MANAGER

    @staticmethod
    def is_hod(user):

        return user.role == Employee.Role.HOD

    @staticmethod
    def is_employee(user):

        return user.role == Employee.Role.EMPLOYEE

    @staticmethod
    def is_admin_or_manager(user):

        return user.role in (
            Employee.Role.ADMIN,
            Employee.Role.ASSET_MANAGER,
        )

    @staticmethod
    def is_admin_manager_or_hod(user):

        return user.role in (
            Employee.Role.ADMIN,
            Employee.Role.ASSET_MANAGER,
            Employee.Role.HOD,
        )

    @staticmethod
    def can_view_assets(user):

        return user.role in (
            Employee.Role.ADMIN,
            Employee.Role.ASSET_MANAGER,
            Employee.Role.HOD,
            Employee.Role.EMPLOYEE,
        )
    # ==========================================================
# Asset Permissions
# ==========================================================

class CanManageAssets(RolePermission):
    """
    Asset Permissions

    GET     -> Everyone
    POST    -> Admin, Asset Manager
    PUT     -> Admin, Asset Manager
    PATCH   -> Admin, Asset Manager
    DELETE  -> Admin
    """

    def check_permission(self, request):

        user = request.user

        if request.method == "GET":
            return self.can_view_assets(user)

        if request.method in ("POST", "PUT", "PATCH"):
            return self.is_admin_or_manager(user)

        if request.method == "DELETE":
            return self.is_admin(user)

        return False


# ==========================================================
# Allocation Permissions
# ==========================================================

class CanManageAllocation(RolePermission):
    """
    Allocation Permissions

    GET     -> Admin, Asset Manager, HOD
    POST    -> Admin, Asset Manager
    PUT     -> Admin, Asset Manager
    PATCH   -> Admin, Asset Manager
    DELETE  -> Admin, Asset Manager
    """

    def check_permission(self, request):

        user = request.user

        if request.method == "GET":
            return self.is_admin_manager_or_hod(user)

        if request.method in (
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        ):
            return self.is_admin_or_manager(user)

        return False
    # ==========================================================
# Transfer Permissions
# ==========================================================

class CanManageTransfer(RolePermission):
    """
    Transfer Permissions

    GET     -> Admin, Asset Manager, HOD
    POST    -> Admin, Asset Manager, HOD
    PUT     -> Admin, Asset Manager
    PATCH   -> Admin, Asset Manager
    DELETE  -> Admin, Asset Manager
    """

    def check_permission(self, request):

        user = request.user

        if request.method in ("GET", "POST"):
            return self.is_admin_manager_or_hod(user)

        if request.method in (
            "PUT",
            "PATCH",
            "DELETE",
        ):
            return self.is_admin_or_manager(user)

        return False


# ==========================================================
# Booking Permissions
# ==========================================================

class CanManageBooking(RolePermission):
    """
    Booking Permissions

    GET     -> Everyone
    POST    -> Everyone
    PUT     -> Admin, Asset Manager
    PATCH   -> Admin, Asset Manager
    DELETE  -> Admin, Asset Manager
    """

    def check_permission(self, request):

        user = request.user

        if request.method in (
            "GET",
            "POST",
        ):
            return self.can_view_assets(user)

        if request.method in (
            "PUT",
            "PATCH",
            "DELETE",
        ):
            return self.is_admin_or_manager(user)

        return False


# ==========================================================
# Maintenance Permissions
# ==========================================================

class CanManageMaintenance(RolePermission):
    """
    Maintenance Permissions

    GET     -> Admin, Asset Manager, HOD
    POST    -> Everyone
    PUT     -> Admin, Asset Manager
    PATCH   -> Admin, Asset Manager
    DELETE  -> Admin, Asset Manager
    """

    def check_permission(self, request):

        user = request.user

        if request.method == "GET":
            return self.is_admin_manager_or_hod(user)

        if request.method == "POST":
            return self.can_view_assets(user)

        if request.method in (
            "PUT",
            "PATCH",
            "DELETE",
        ):
            return self.is_admin_or_manager(user)

        return False