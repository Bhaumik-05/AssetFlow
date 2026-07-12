from django.db.models.signals import post_save
from django.dispatch import receiver

from assets.models import (
    AssetAllocation,
    ResourceBooking,
    MaintenanceRequest,
    AssetTransfer,
)
from audits.models import AuditCycle

from .service import create_notification


# ==========================================================
# Asset Allocation
# ==========================================================

@receiver(post_save, sender=AssetAllocation)
def notify_asset_allocation(sender, instance, created, **kwargs):

    if created and instance.employee:

        create_notification(
            employee=instance.employee,
            title="Asset Allocated",
            message=f"{instance.asset.asset_code} has been allocated to you."
        )


# ==========================================================
# Asset Return
# ==========================================================

@receiver(post_save, sender=AssetAllocation)
def notify_asset_return(sender, instance, created, **kwargs):

    if (
        not created
        and instance.status == AssetAllocation.Status.RETURNED
        and instance.employee
    ):

        create_notification(
            employee=instance.employee,
            title="Asset Returned",
            message=f"{instance.asset.asset_code} has been successfully returned."
        )


# ==========================================================
# Booking Approved
# ==========================================================

@receiver(post_save, sender=ResourceBooking)
def notify_booking_approved(sender, instance, created, **kwargs):

    if (
        not created
        and instance.status == ResourceBooking.Status.APPROVED
    ):

        create_notification(
            employee=instance.employee,
            title="Booking Approved",
            message=(
                f"Your booking for "
                f"{instance.asset.asset_code} has been approved."
            )
        )


# ==========================================================
# Maintenance Approved
# ==========================================================

@receiver(post_save, sender=MaintenanceRequest)
def notify_maintenance_approved(sender, instance, created, **kwargs):

    if (
        not created
        and instance.status == MaintenanceRequest.Status.APPROVED
    ):

        create_notification(
            employee=instance.reported_by,
            title="Maintenance Approved",
            message=(
                f"Maintenance request for "
                f"{instance.asset.asset_code} has been approved."
            )
        )


# ==========================================================
# Transfer Approved
# ==========================================================

@receiver(post_save, sender=AssetTransfer)
def notify_transfer_approved(sender, instance, created, **kwargs):

    if (
        not created
        and instance.status == AssetTransfer.Status.APPROVED
    ):

        # Notify destination employee if present,
        # otherwise notify requester.

        employee = (
            instance.to_employee
            if instance.to_employee
            else instance.requested_by
        )

        create_notification(
            employee=employee,
            title="Transfer Approved",
            message=(
                f"Transfer request for "
                f"{instance.asset.asset_code} has been approved."
            )
        )


# ==========================================================
# Audit Completed
# ==========================================================

@receiver(post_save, sender=AuditCycle)
def notify_audit_completed(sender, instance, created, **kwargs):

    if (
        not created
        and instance.status == AuditCycle.Status.COMPLETED
    ):

        create_notification(
            employee=instance.conducted_by,
            title="Audit Completed",
            message=(
                f'Audit "{instance.title}" has been completed successfully.'
            )
        )