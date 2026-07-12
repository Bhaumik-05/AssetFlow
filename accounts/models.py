from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser


class Department(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    code = models.CharField(
        max_length=10,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    hod = models.OneToOneField(
        "Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_department"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return self.name

from .managers import EmployeeManager
class Employee(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        ASSET_MANAGER = "ASSET_MANAGER", "Asset Manager"
        HOD = "HOD", "Head of Department"
        EMPLOYEE = "EMPLOYEE", "Employee"

    username = None

    employee_id = models.CharField(
        max_length=20,
        unique=True
    )

    email = models.EmailField(
        unique=True
    )

    phone = models.CharField(
        max_length=15,
        unique=True
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "employee_id"
    ]
    objects = EmployeeManager()

    class Meta:
        ordering = ["first_name", "last_name"]
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"