from django.db import models

from accounts.models import Department, Employee
from assets.models import Asset


class AuditCycle(models.Model):

    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=150)

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="audit_cycles"
    )

    start_date = models.DateField()
    end_date = models.DateField()

    conducted_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="conducted_audits"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "Audit Cycle"
        verbose_name_plural = "Audit Cycles"

    def __str__(self):
        return self.title


class AuditRecord(models.Model):

    class Condition(models.TextChoices):
        NEW = "NEW", "New"
        GOOD = "GOOD", "Good"
        FAIR = "FAIR", "Fair"
        DAMAGED = "DAMAGED", "Damaged"

    class Status(models.TextChoices):
        VERIFIED = "VERIFIED", "Verified"
        MISSING = "MISSING", "Missing"
        DAMAGED = "DAMAGED", "Damaged"

    audit_cycle = models.ForeignKey(
        AuditCycle,
        on_delete=models.CASCADE,
        related_name="audit_records"
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="audit_records"
    )

    verified_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="verified_audit_records"
    )

    condition = models.CharField(
        max_length=20,
        choices=Condition.choices
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.VERIFIED
    )

    remarks = models.TextField(blank=True)

    verified_on = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-verified_on"]
        verbose_name = "Audit Record"
        verbose_name_plural = "Audit Records"

        constraints = [
            models.UniqueConstraint(
                fields=["audit_cycle", "asset"],
                name="unique_asset_per_audit_cycle"
            )
        ]

    def __str__(self):
        return f"{self.asset.asset_code} - {self.audit_cycle.title}"