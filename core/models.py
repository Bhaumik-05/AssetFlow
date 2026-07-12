from django.db import models
from accounts.models import Employee


class Notification(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.title} - {self.employee.email}"


class ActivityLog(models.Model):

    class Module(models.TextChoices):
        ACCOUNT = "ACCOUNT", "Account"
        ASSET = "ASSET", "Asset"
        ALLOCATION = "ALLOCATION", "Allocation"
        TRANSFER = "TRANSFER", "Transfer"
        BOOKING = "BOOKING", "Booking"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        AUDIT = "AUDIT", "Audit"

    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs"
    )

    action = models.CharField(
        max_length=255
    )

    module = models.CharField(
        max_length=20,
        choices=Module.choices
    )

    object_id = models.PositiveBigIntegerField()

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    ip_address = models.GenericIPAddressField()

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"

    def __str__(self):
        return f"{self.employee} - {self.action}"