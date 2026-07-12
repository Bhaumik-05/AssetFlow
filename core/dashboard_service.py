from accounts.models import Employee, Department
from assets.models import (
    Asset,
    AssetAllocation,
    AssetTransfer,
    MaintenanceRequest,
    ResourceBooking,
)
from audits.models import AuditCycle


class DashboardService:

    @staticmethod
    def admin_dashboard():
        return {
            "total_assets": Asset.objects.count(),

            "available_assets": Asset.objects.filter(
                status=Asset.Status.AVAILABLE
            ).count(),

            "allocated_assets": Asset.objects.filter(
                status=Asset.Status.ALLOCATED
            ).count(),

            "departments": Department.objects.filter(
                is_active=True
            ).count(),

            "employees": Employee.objects.filter(
                is_active=True
            ).count(),

            # Only currently running audits
            "active_audits": AuditCycle.objects.filter(
                status=AuditCycle.Status.IN_PROGRESS
            ).count(),
        }

    @staticmethod
    def asset_manager_dashboard():
        return {
            "available_assets": Asset.objects.filter(
                status=Asset.Status.AVAILABLE
            ).count(),

            "pending_maintenance": MaintenanceRequest.objects.filter(
                status=MaintenanceRequest.Status.PENDING
            ).count(),

            "pending_transfers": AssetTransfer.objects.filter(
                status=AssetTransfer.Status.PENDING
            ).count(),

            "pending_bookings": ResourceBooking.objects.filter(
                status=ResourceBooking.Status.PENDING
            ).count(),
        }

    @staticmethod
    def hod_dashboard(user):
        department = user.department

        return {
            "department_assets": Asset.objects.filter(
                department=department
            ).count(),

            "department_employees": Employee.objects.filter(
                department=department,
                is_active=True
            ).count(),

            "pending_maintenance": MaintenanceRequest.objects.filter(
                asset__department=department,
                status=MaintenanceRequest.Status.PENDING
            ).count(),

            "pending_transfers": AssetTransfer.objects.filter(
                to_department=department,
                status=AssetTransfer.Status.PENDING
            ).count(),
        }

    @staticmethod
    def employee_dashboard(user):
        return {
            "my_assets": AssetAllocation.objects.filter(
                employee=user,
                status=AssetAllocation.Status.ACTIVE
            ).count(),

            # Count only active bookings
            "my_bookings": ResourceBooking.objects.filter(
                employee=user
            ).exclude(
                status=ResourceBooking.Status.CANCELLED
            ).count(),

            "my_maintenance_requests": MaintenanceRequest.objects.filter(
                reported_by=user
            ).count(),

            "my_transfer_requests": AssetTransfer.objects.filter(
                requested_by=user
            ).count(),
        }