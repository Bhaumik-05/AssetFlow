from accounts.models import Department
from assets.models import (
    Asset,
    AssetTransfer,
    MaintenanceRequest,
    ResourceBooking,
)
from audits.models import AuditCycle, AuditRecord


class ReportService:

    # =====================================================
    # Asset Utilization Report
    # =====================================================

    @staticmethod
    def asset_utilization():

        return {

            "total_assets": Asset.objects.count(),

            "available_assets": Asset.objects.filter(
                status=Asset.Status.AVAILABLE
            ).count(),

            "allocated_assets": Asset.objects.filter(
                status=Asset.Status.ALLOCATED
            ).count(),

            "reserved_assets": Asset.objects.filter(
                status=Asset.Status.RESERVED
            ).count(),

            "under_maintenance": Asset.objects.filter(
                status=Asset.Status.UNDER_MAINTENANCE
            ).count(),

            "lost_assets": Asset.objects.filter(
                status=Asset.Status.LOST
            ).count(),

            "retired_assets": Asset.objects.filter(
                status=Asset.Status.RETIRED
            ).count(),

            "disposed_assets": Asset.objects.filter(
                status=Asset.Status.DISPOSED
            ).count(),
        }

    # =====================================================
    # Department-wise Asset Report
    # =====================================================

    @staticmethod
    def department_asset_report():

        report = []

        departments = Department.objects.filter(
            is_active=True
        ).order_by("name")

        for department in departments:

            assets = department.assets.all()

            report.append({

                "department": department.name,

                "department_code": department.code,

                "total_assets": assets.count(),

                "available_assets": assets.filter(
                    status=Asset.Status.AVAILABLE
                ).count(),

                "allocated_assets": assets.filter(
                    status=Asset.Status.ALLOCATED
                ).count(),

                "reserved_assets": assets.filter(
                    status=Asset.Status.RESERVED
                ).count(),

                "under_maintenance": assets.filter(
                    status=Asset.Status.UNDER_MAINTENANCE
                ).count(),

                "lost_assets": assets.filter(
                    status=Asset.Status.LOST
                ).count(),

                "retired_assets": assets.filter(
                    status=Asset.Status.RETIRED
                ).count(),

                "disposed_assets": assets.filter(
                    status=Asset.Status.DISPOSED
                ).count(),

            })

        return report

    # =====================================================
    # Maintenance Statistics
    # =====================================================

    @staticmethod
    def maintenance_statistics():

        return {

            "total_requests": MaintenanceRequest.objects.count(),

            "pending": MaintenanceRequest.objects.filter(
                status=MaintenanceRequest.Status.PENDING
            ).count(),

            "approved": MaintenanceRequest.objects.filter(
                status=MaintenanceRequest.Status.APPROVED
            ).count(),

            "in_progress": MaintenanceRequest.objects.filter(
                status=MaintenanceRequest.Status.IN_PROGRESS
            ).count(),

            "resolved": MaintenanceRequest.objects.filter(
                status=MaintenanceRequest.Status.RESOLVED
            ).count(),

            "rejected": MaintenanceRequest.objects.filter(
                status=MaintenanceRequest.Status.REJECTED
            ).count(),

        }

    # =====================================================
    # Booking Statistics
    # =====================================================

    @staticmethod
    def booking_statistics():

        return {

            "total_bookings": ResourceBooking.objects.count(),

            "pending": ResourceBooking.objects.filter(
                status=ResourceBooking.Status.PENDING
            ).count(),

            "approved": ResourceBooking.objects.filter(
                status=ResourceBooking.Status.APPROVED
            ).count(),

            "cancelled": ResourceBooking.objects.filter(
                status=ResourceBooking.Status.CANCELLED
            ).count(),

            "completed": ResourceBooking.objects.filter(
                status=ResourceBooking.Status.COMPLETED
            ).count(),

        }

    # =====================================================
    # Transfer Statistics
    # =====================================================

    @staticmethod
    def transfer_statistics():

        return {

            "total_transfers": AssetTransfer.objects.count(),

            "pending": AssetTransfer.objects.filter(
                status=AssetTransfer.Status.PENDING
            ).count(),

            "approved": AssetTransfer.objects.filter(
                status=AssetTransfer.Status.APPROVED
            ).count(),

            "rejected": AssetTransfer.objects.filter(
                status=AssetTransfer.Status.REJECTED
            ).count(),

            "completed": AssetTransfer.objects.filter(
                status=AssetTransfer.Status.COMPLETED
            ).count(),

        }

    # =====================================================
    # Audit Statistics
    # =====================================================

    @staticmethod
    def audit_statistics():

        return {

            "total_audits": AuditCycle.objects.count(),

            "planned": AuditCycle.objects.filter(
                status=AuditCycle.Status.PLANNED
            ).count(),

            "in_progress": AuditCycle.objects.filter(
                status=AuditCycle.Status.IN_PROGRESS
            ).count(),

            "completed": AuditCycle.objects.filter(
                status=AuditCycle.Status.COMPLETED
            ).count(),

            "total_records": AuditRecord.objects.count(),

            "verified_records": AuditRecord.objects.filter(
                status=AuditRecord.Status.VERIFIED
            ).count(),

            "missing_records": AuditRecord.objects.filter(
                status=AuditRecord.Status.MISSING
            ).count(),

            "damaged_records": AuditRecord.objects.filter(
                status=AuditRecord.Status.DAMAGED
            ).count(),

        }