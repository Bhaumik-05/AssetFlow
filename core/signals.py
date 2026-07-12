from django.db.models.signals import post_save
from django.dispatch import receiver

from assets.models import AssetAllocation
from .service import create_notification


@receiver(post_save, sender=AssetAllocation)
def notify_asset_allocation(sender, instance, created, **kwargs):

    if created and instance.employee:

        asset_code = (
            instance.asset.asset_code
            if instance.asset
            else "Asset"
        )

        create_notification(
            employee=instance.employee,
            title="Asset Allocated",
            message=f"{asset_code} has been allocated to you."
        )