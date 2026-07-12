from rest_framework.permissions import BasePermission, SAFE_METHODS


# =====================================================
# Basic Role Permissions
# =====================================================

class IsAdmin(BasePermission):
    """
    Allows access only to Admin users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "ADMIN"
        )


class IsAssetManager(BasePermission):
    """
    Allows access only to Asset Managers.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "ASSET_MANAGER"
        )


class IsHOD(BasePermission):
    """
    Allows access only to HOD.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "HOD"
        )


class IsEmployee(BasePermission):
    """
    Allows access only to Employees.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "EMPLOYEE"
        )


# =====================================================
# Combined Role Permissions
# =====================================================

class IsAdminOrAssetManager(BasePermission):
    """
    Admin or Asset Manager.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in [
                "ADMIN",
                "ASSET_MANAGER",
            ]
        )


class IsAdminOrHOD(BasePermission):
    """
    Admin or HOD.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in [
                "ADMIN",
                "HOD",
            ]
        )


class IsAdminOrAssetManagerOrHOD(BasePermission):
    """
    Admin, Asset Manager or HOD.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in [
                "ADMIN",
                "ASSET_MANAGER",
                "HOD",
            ]
        )


# =====================================================
# Read Only Permission
# =====================================================

class ReadOnly(BasePermission):
    """
    Allows only GET, HEAD and OPTIONS requests.
    """

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


# =====================================================
# Admin Full Access
# Others Read Only
# =====================================================

class AdminOrReadOnly(BasePermission):
    """
    Everyone can view.
    Only Admin can modify.
    """

    def has_permission(self, request, view):

        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        return (
            request.user.is_authenticated and
            request.user.role == "ADMIN"
        )


# =====================================================
# Asset Manager Full Access
# Others Read Only
# =====================================================

class AssetManagerOrReadOnly(BasePermission):
    """
    Everyone can view.
    Only Asset Manager can modify.
    """

    def has_permission(self, request, view):

        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        return (
            request.user.is_authenticated and
            request.user.role == "ASSET_MANAGER"
        )


# =====================================================
# Employee Own Object Permission
# =====================================================

class IsOwner(BasePermission):
    """
    Employee can access only their own object.
    Admin has full access.
    """

    def has_object_permission(self, request, view, obj):

        if request.user.role == "ADMIN":
            return True

        return obj == request.user


# =====================================================
# Employee Own Request Permission
# =====================================================

class IsRequestOwner(BasePermission):
    """
    Employee can manage only their own requests.
    Admin can access everything.
    """

    def has_object_permission(self, request, view, obj):

        if request.user.role == "ADMIN":
            return True

        return obj.employee == request.user


# =====================================================
# HOD Department Permission
# =====================================================

class IsSameDepartmentHOD(BasePermission):
    """
    HOD can access only employees/assets
    belonging to their department.
    """

    def has_object_permission(self, request, view, obj):

        if request.user.role == "ADMIN":
            return True

        if request.user.role != "HOD":
            return False

        return (
            request.user.department ==
            obj.department
        )


# =====================================================
# Asset Manager Permission
# =====================================================

class CanManageAssets(BasePermission):
    """
    Only Asset Manager can register/update/delete assets.
    Admin has full access.
    """

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated and
            request.user.role in [
                "ADMIN",
                "ASSET_MANAGER",
            ]
        )


# =====================================================
# Department Approval Permission
# =====================================================

class CanApproveDepartmentRequests(BasePermission):
    """
    Admin and HOD can approve requests.
    """

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated and
            request.user.role in [
                "ADMIN",
                "HOD",
            ]
        )


# =====================================================
# Assign Roles Permission
# =====================================================

class CanAssignRoles(BasePermission):
    """
    Only Admin can assign/change roles.
    """

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated and
            request.user.role == "ADMIN"
        )


# =====================================================
# Department Management Permission
# =====================================================

class CanManageDepartments(BasePermission):
    """
    Only Admin can create/update/delete departments.
    """

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated and
            request.user.role == "ADMIN"
        )


# =====================================================
# Employee Management Permission
# =====================================================

class CanManageEmployees(BasePermission):
    """
    Only Admin can create/update/deactivate employees.
    """

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated and
            request.user.role == "ADMIN"
        )


# =====================================================
# Super Permission
# =====================================================

class IsAdminOrSelf(BasePermission):
    """
    Admin can access everything.
    Employee can access only their own profile.
    """

    def has_object_permission(self, request, view, obj):

        if request.user.role == "ADMIN":
            return True

        return obj == request.user