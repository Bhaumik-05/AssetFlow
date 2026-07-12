from django.db import models

# Create your models here.

from django.db import models
from accounts.models import Employee, Department


class AssetCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Asset Category"
        verbose_name_plural = "Asset Categories"

    def __str__(self):
        return self.name


class Asset(models.Model):

    class Condition(models.TextChoices):
        NEW = "NEW", "New"
        GOOD = "GOOD", "Good"
        FAIR = "FAIR", "Fair"
        DAMAGED = "DAMAGED", "Damaged"

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        ALLOCATED = "ALLOCATED", "Allocated"
        RESERVED = "RESERVED", "Reserved"
        UNDER_MAINTENANCE = "UNDER_MAINTENANCE", "Under Maintenance"
        LOST = "LOST", "Lost"
        RETIRED = "RETIRED", "Retired"
        DISPOSED = "DISPOSED", "Disposed"

    asset_code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)

    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.PROTECT,
        related_name="assets"
    )

    serial_number = models.CharField(max_length=100, unique=True)

    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    purchase_date = models.DateField()

    purchase_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.NEW
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.AVAILABLE
    )

    location = models.CharField(max_length=150)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets"
    )

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["asset_code"]

    def __str__(self):
        return f"{self.asset_code} - {self.name}"


class AssetAllocation(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        RETURNED = "RETURNED", "Returned"
        CANCELLED = "CANCELLED", "Cancelled"

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="allocations"
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asset_allocations"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="asset_allocations"
    )

    allocated_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="allocated_assets"
    )

    allocated_on = models.DateTimeField(auto_now_add=True)

    expected_return_date = models.DateField(
        null=True,
        blank=True
    )

    returned_on = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-allocated_on"]

    def __str__(self):
        return f"{self.asset.asset_code} -> {self.department.name}"


class AssetTransfer(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        COMPLETED = "COMPLETED", "Completed"

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="transfers"
    )

    from_department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="outgoing_transfers"
    )

    to_department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="incoming_transfers"
    )

    from_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_from"
    )

    to_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_to"
    )

    requested_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="requested_transfers"
    )

    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_transfers"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    reason = models.TextField()

    request_date = models.DateTimeField(auto_now_add=True)

    approved_date = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-request_date"]

    def __str__(self):
        return f"Transfer - {self.asset.asset_code}"


class ResourceBooking(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        CANCELLED = "CANCELLED", "Cancelled"

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="resource_bookings"
    )

    purpose = models.TextField()

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_datetime"]

    def __str__(self):
        return f"{self.asset.name} Booking"


class MaintenanceRequest(models.Model):

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="maintenance_requests"
    )

    reported_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="reported_maintenance"
    )

    issue = models.TextField()

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    assigned_to = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_maintenance"
    )

    reported_on = models.DateTimeField(auto_now_add=True)

    resolved_on = models.DateTimeField(
        null=True,
        blank=True
    )

    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-reported_on"]

    def __str__(self):
        return f"Maintenance - {self.asset.asset_code}"