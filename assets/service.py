from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import Employee, Department
from assets.models import Asset, AssetAllocation


class AllocationService:

    # ==========================================================
    # Helper Methods
    # ==========================================================

    @staticmethod
    def _validate_asset(asset):

        if not isinstance(asset, Asset):
            raise ValidationError("Invalid asset.")

        return asset

    @staticmethod
    def _validate_employee(employee):

        if employee is None:
            return None

        if not isinstance(employee, Employee):
            raise ValidationError("Invalid employee.")

        if not employee.is_active:
            raise ValidationError(
                "Employee is inactive."
            )

        return employee

    @staticmethod
    def _validate_department(department):

        if not isinstance(department, Department):
            raise ValidationError(
                "Invalid department."
            )

        return department

    @staticmethod
    def _validate_allocator(employee):

        if not isinstance(employee, Employee):
            raise ValidationError(
                "Invalid allocator."
            )

        if employee.role not in [
            Employee.Role.ADMIN,
            Employee.Role.ASSET_MANAGER
        ]:

            raise ValidationError(
                "Only Admin or Asset Manager can allocate assets."
            )

        return employee

    @staticmethod
    def has_active_allocation(asset):

        return AssetAllocation.objects.filter(
            asset=asset,
            status=AssetAllocation.Status.ACTIVE
        ).exists()

    # ==========================================================
    # Allocate Asset
    # ==========================================================

    @staticmethod
    @transaction.atomic
    def allocate_asset(
        *,
        asset,
        department,
        allocated_by,
        employee=None,
        expected_return_date=None,
        remarks=""
    ):

        asset = AllocationService._validate_asset(asset)

        employee = AllocationService._validate_employee(
            employee
        )

        department = AllocationService._validate_department(
            department
        )

        allocated_by = AllocationService._validate_allocator(
            allocated_by
        )

        # --------------------------------------------
        # Asset Status Validation
        # --------------------------------------------

        if asset.status != Asset.Status.AVAILABLE:

            raise ValidationError(
                f"Asset is currently {asset.status.lower()}."
            )

        # --------------------------------------------
        # Duplicate Allocation
        # --------------------------------------------

        if AllocationService.has_active_allocation(
            asset
        ):

            raise ValidationError(
                "Asset already has an active allocation."
            )

        # --------------------------------------------
        # Department Validation
        # --------------------------------------------

        if employee:

            if employee.department != department:

                raise ValidationError(
                    "Employee does not belong to selected department."
                )

        # --------------------------------------------
        # Expected Return Date
        # --------------------------------------------

        if expected_return_date:

            if expected_return_date < date.today():

                raise ValidationError(
                    "Expected return date cannot be in past."
                )

        # --------------------------------------------
        # Remarks
        # --------------------------------------------

        if remarks:

            remarks = remarks.strip()

            if len(remarks) > 1000:

                raise ValidationError(
                    "Remarks too long."
                )

        # --------------------------------------------
        # Create Allocation
        # --------------------------------------------

        allocation = AssetAllocation.objects.create(

            asset=asset,

            employee=employee,

            department=department,

            allocated_by=allocated_by,

            expected_return_date=expected_return_date,

            remarks=remarks,

            status=AssetAllocation.Status.ACTIVE

        )

        # --------------------------------------------
        # Update Asset
        # --------------------------------------------

        asset.department = department

        asset.status = Asset.Status.ALLOCATED

        asset.full_clean()

        asset.save(
            update_fields=[
                "department",
                "status",
                "updated_at"
            ]
        )

        return allocation
    
        # ==========================================================
    # Return Asset
    # ==========================================================

    @staticmethod
    @transaction.atomic
    def return_asset(
        *,
        asset,
        returned_on=None,
        remarks=""
    ):
        """
        Returns an allocated asset.

        Business Rules:
        ----------------
        • Asset must have an active allocation.
        • Asset status must be ALLOCATED.
        • Closes allocation history.
        • Makes asset AVAILABLE again.
        • Removes department ownership.
        """

        asset = AllocationService._validate_asset(asset)

        if asset.status != Asset.Status.ALLOCATED:

            raise ValidationError(
                "Only allocated assets can be returned."
            )

        allocation = (
            AssetAllocation.objects
            .select_for_update()
            .filter(
                asset=asset,
                status=AssetAllocation.Status.ACTIVE
            )
            .first()
        )

        if not allocation:

            raise ValidationError(
                "No active allocation found."
            )

        if returned_on is None:
            returned_on = date.today()

        if allocation.allocated_on.date() > returned_on:

            raise ValidationError(
                "Return date cannot be before allocation date."
            )

        if (
            allocation.expected_return_date
            and returned_on < allocation.expected_return_date
        ):
            # Returning early is allowed.
            pass

        if remarks:

            remarks = remarks.strip()

            if len(remarks) > 1000:

                raise ValidationError(
                    "Remarks exceed maximum length."
                )

        # --------------------------------------
        # Close Allocation
        # --------------------------------------

        allocation.returned_on = returned_on
        allocation.status = AssetAllocation.Status.RETURNED

        if remarks:
            allocation.remarks = remarks

        allocation.full_clean()
        allocation.save()

        # --------------------------------------
        # Update Asset
        # --------------------------------------

        asset.department = None
        asset.status = Asset.Status.AVAILABLE

        asset.full_clean()

        asset.save(
            update_fields=[
                "department",
                "status",
                "updated_at",
            ]
        )

        return allocation
    

        # ==========================================================
    # Cancel Allocation
    # ==========================================================

    @staticmethod
    @transaction.atomic
    def cancel_allocation(
        *,
        allocation,
        remarks=""
    ):
        """
        Cancel an active allocation.

        Rules
        -----
        • Only ACTIVE allocations can be cancelled.
        • Asset becomes AVAILABLE.
        • Department ownership is removed.
        """

        if not isinstance(allocation, AssetAllocation):
            raise ValidationError(
                "Invalid allocation."
            )

        if allocation.status != AssetAllocation.Status.ACTIVE:
            raise ValidationError(
                "Only active allocations can be cancelled."
            )

        asset = allocation.asset

        allocation.status = AssetAllocation.Status.CANCELLED

        if remarks:
            remarks = remarks.strip()

            if len(remarks) > 1000:
                raise ValidationError(
                    "Remarks exceed maximum length."
                )

            allocation.remarks = remarks

        allocation.full_clean()
        allocation.save()

        asset.status = Asset.Status.AVAILABLE
        asset.department = None

        asset.full_clean()

        asset.save(
            update_fields=[
                "status",
                "department",
                "updated_at"
            ]
        )

        return allocation


    # ==========================================================
    # Current Allocation
    # ==========================================================

    @staticmethod
    def get_current_allocation(asset):
        """
        Returns current active allocation.
        """

        asset = AllocationService._validate_asset(asset)

        return (
            AssetAllocation.objects
            .select_related(
                "employee",
                "department",
                "allocated_by"
            )
            .filter(
                asset=asset,
                status=AssetAllocation.Status.ACTIVE
            )
            .first()
        )


    # ==========================================================
    # Allocation History
    # ==========================================================

    @staticmethod
    def allocation_history(asset):

        asset = AllocationService._validate_asset(asset)

        return (
            AssetAllocation.objects
            .select_related(
                "employee",
                "department",
                "allocated_by"
            )
            .filter(
                asset=asset
            )
            .order_by(
                "-allocated_on"
            )
        )


    # ==========================================================
    # Helper Methods
    # ==========================================================

    @staticmethod
    def is_allocated(asset):

        asset = AllocationService._validate_asset(asset)

        return asset.status == Asset.Status.ALLOCATED


    @staticmethod
    def active_allocation(asset):

        return (
            AssetAllocation.objects
            .filter(
                asset=asset,
                status=AssetAllocation.Status.ACTIVE
            )
            .exists()
        )


    @staticmethod
    def employee_assets(employee):

        employee = AllocationService._validate_employee(
            employee
        )

        return (
            AssetAllocation.objects
            .select_related(
                "asset",
                "department"
            )
            .filter(
                employee=employee,
                status=AssetAllocation.Status.ACTIVE
            )
        )


    @staticmethod
    def department_assets(department):

        department = (
            AllocationService._validate_department(
                department
            )
        )

        return (
            AssetAllocation.objects
            .select_related(
                "asset",
                "employee"
            )
            .filter(
                department=department,
                status=AssetAllocation.Status.ACTIVE
            )
        )


    @staticmethod
    def overdue_allocations():

        return (
            AssetAllocation.objects
            .select_related(
                "asset",
                "employee",
                "department"
            )
            .filter(
                status=AssetAllocation.Status.ACTIVE,
                expected_return_date__lt=date.today()
            )
        )
    
 import re
from decimal import Decimal
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max

from accounts.models import Department
from assets.models import Asset, AssetCategory


class AssetService:
    """
    Business Logic for Asset CRUD Operations
    """

    ASSET_PREFIX = "AST"

    # --------------------------------------------------------
    # Asset Code Generator
    # --------------------------------------------------------

    @staticmethod
    def generate_asset_code():
        """
        Generates codes like:

        AST000001
        AST000002
        """

        last_asset = (
            Asset.objects
            .order_by("-id")
            .only("asset_code")
            .first()
        )

        if not last_asset:
            return f"{AssetService.ASSET_PREFIX}000001"

        try:
            number = int(last_asset.asset_code.replace(
                AssetService.ASSET_PREFIX,
                ""
            ))
        except Exception:
            raise ValidationError(
                "Existing asset code format is invalid."
            )

        return f"{AssetService.ASSET_PREFIX}{number + 1:06d}"

    # --------------------------------------------------------
    # Validation Helpers
    # --------------------------------------------------------

    @staticmethod
    def _validate_name(name):

        if not name:
            raise ValidationError("Asset name is required.")

        name = name.strip()

        if len(name) < 3:
            raise ValidationError(
                "Asset name is too short."
            )

        if len(name) > 150:
            raise ValidationError(
                "Asset name exceeds maximum length."
            )

        return name

    @staticmethod
    def _validate_manufacturer(manufacturer):

        if not manufacturer:
            raise ValidationError(
                "Manufacturer is required."
            )

        manufacturer = manufacturer.strip()

        pattern = r"^[A-Za-z0-9 .,&()-]+$"

        if not re.match(pattern, manufacturer):
            raise ValidationError(
                "Invalid manufacturer name."
            )

        return manufacturer

    @staticmethod
    def _validate_model(model):

        if not model:
            raise ValidationError(
                "Model is required."
            )

        model = model.strip()

        pattern = r"^[A-Za-z0-9 .,_-]+$"

        if not re.match(pattern, model):
            raise ValidationError(
                "Invalid model."
            )

        return model

    @staticmethod
    def _validate_serial_number(serial):

        if not serial:
            raise ValidationError(
                "Serial number is required."
            )

        serial = serial.strip()

        if len(serial) < 3:
            raise ValidationError(
                "Serial number is invalid."
            )

        if Asset.objects.filter(
            serial_number__iexact=serial
        ).exists():

            raise ValidationError(
                "Serial number already exists."
            )

        return serial

    @staticmethod
    def _validate_purchase_date(purchase_date):

        if purchase_date > date.today():

            raise ValidationError(
                "Purchase date cannot be in future."
            )

        return purchase_date

    @staticmethod
    def _validate_purchase_cost(cost):

        try:
            cost = Decimal(cost)

        except Exception:
            raise ValidationError(
                "Invalid purchase cost."
            )

        if cost <= 0:
            raise ValidationError(
                "Purchase cost must be greater than zero."
            )

        return cost

    @staticmethod
    def _validate_category(category):

        if not isinstance(category, AssetCategory):

            raise ValidationError(
                "Invalid asset category."
            )

        return category

    @staticmethod
    def _validate_department(department):

        if department is None:
            return None

        if not isinstance(department, Department):

            raise ValidationError(
                "Invalid department."
            )

        return department

    @staticmethod
    def _validate_condition(condition):

        if condition not in Asset.Condition.values:

            raise ValidationError(
                "Invalid asset condition."
            )

        return condition

    @staticmethod
    def _validate_status(status):

        if status not in Asset.Status.values:

            raise ValidationError(
                "Invalid asset status."
            )

        return status
    
        # --------------------------------------------------------
    # Create Asset
    # --------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def create_asset(
        *,
        name,
        category,
        serial_number,
        manufacturer,
        model,
        purchase_date,
        purchase_cost,
        location,
        department=None,
        remarks="",
        condition=Asset.Condition.NEW,
        status=Asset.Status.AVAILABLE
    ):
        """
        Creates a new asset after validating all business rules.
        """

        try:

            # -----------------------------
            # Required Validations
            # -----------------------------

            name = AssetService._validate_name(name)

            category = AssetService._validate_category(
                category
            )

            serial_number = (
                AssetService._validate_serial_number(
                    serial_number
                )
            )

            manufacturer = (
                AssetService._validate_manufacturer(
                    manufacturer
                )
            )

            model = AssetService._validate_model(
                model
            )

            purchase_date = (
                AssetService._validate_purchase_date(
                    purchase_date
                )
            )

            purchase_cost = (
                AssetService._validate_purchase_cost(
                    purchase_cost
                )
            )

            department = (
                AssetService._validate_department(
                    department
                )
            )

            condition = (
                AssetService._validate_condition(
                    condition
                )
            )

            status = (
                AssetService._validate_status(
                    status
                )
            )

            # -----------------------------
            # Location Validation
            # -----------------------------

            if not location:
                raise ValidationError(
                    "Location is required."
                )

            location = location.strip()

            if len(location) < 2:
                raise ValidationError(
                    "Invalid location."
                )

            if len(location) > 150:
                raise ValidationError(
                    "Location exceeds maximum length."
                )

            # -----------------------------
            # Remarks
            # -----------------------------

            if remarks:
                remarks = remarks.strip()

                if len(remarks) > 1000:
                    raise ValidationError(
                        "Remarks exceed allowed length."
                    )

            # -----------------------------
            # Asset Code
            # -----------------------------

            asset_code = (
                AssetService.generate_asset_code()
            )

            # -----------------------------
            # Create Object
            # -----------------------------

            asset = Asset(

                asset_code=asset_code,

                name=name,

                category=category,

                serial_number=serial_number,

                manufacturer=manufacturer,

                model=model,

                purchase_date=purchase_date,

                purchase_cost=purchase_cost,

                condition=condition,

                status=status,

                location=location,

                department=department,

                remarks=remarks

            )

            # -----------------------------
            # Django Validation
            # -----------------------------

            asset.full_clean()

            asset.save()

            return asset

        except ValidationError:
            raise

        except Exception as e:

            raise ValidationError(
                f"Unable to create asset : {str(e)}"
            )
        


            # --------------------------------------------------------
    # Update Asset
    # --------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def update_asset(asset: Asset, **kwargs):
        """
        Update asset details.

        Business Rules:
        - Asset Code cannot be changed.
        - Retired/Disposed assets cannot be edited.
        - Duplicate serial numbers are not allowed.
        - Every modified field is validated.
        """

        if not isinstance(asset, Asset):
            raise ValidationError("Invalid asset instance.")

        if asset.status in [
            Asset.Status.RETIRED,
            Asset.Status.DISPOSED,
        ]:
            raise ValidationError(
                "Retired or disposed assets cannot be modified."
            )

        editable_fields = {
            "name",
            "category",
            "serial_number",
            "manufacturer",
            "model",
            "purchase_date",
            "purchase_cost",
            "condition",
            "status",
            "location",
            "department",
            "remarks",
        }

        invalid_fields = set(kwargs.keys()) - editable_fields

        if invalid_fields:
            raise ValidationError(
                f"Invalid fields: {', '.join(invalid_fields)}"
            )

        # ----------------------------
        # Name
        # ----------------------------

        if "name" in kwargs:
            asset.name = AssetService._validate_name(
                kwargs["name"]
            )

        # ----------------------------
        # Category
        # ----------------------------

        if "category" in kwargs:
            asset.category = (
                AssetService._validate_category(
                    kwargs["category"]
                )
            )

        # ----------------------------
        # Serial Number
        # ----------------------------

        if "serial_number" in kwargs:

            serial = kwargs["serial_number"].strip()

            duplicate = Asset.objects.filter(
                serial_number__iexact=serial
            ).exclude(
                pk=asset.pk
            )

            if duplicate.exists():
                raise ValidationError(
                    "Serial number already exists."
                )

            asset.serial_number = serial

        # ----------------------------
        # Manufacturer
        # ----------------------------

        if "manufacturer" in kwargs:

            asset.manufacturer = (
                AssetService._validate_manufacturer(
                    kwargs["manufacturer"]
                )
            )

        # ----------------------------
        # Model
        # ----------------------------

        if "model" in kwargs:

            asset.model = AssetService._validate_model(
                kwargs["model"]
            )

        # ----------------------------
        # Purchase Date
        # ----------------------------

        if "purchase_date" in kwargs:

            asset.purchase_date = (
                AssetService._validate_purchase_date(
                    kwargs["purchase_date"]
                )
            )

        # ----------------------------
        # Purchase Cost
        # ----------------------------

        if "purchase_cost" in kwargs:

            asset.purchase_cost = (
                AssetService._validate_purchase_cost(
                    kwargs["purchase_cost"]
                )
            )

        # ----------------------------
        # Condition
        # ----------------------------

        if "condition" in kwargs:

            asset.condition = (
                AssetService._validate_condition(
                    kwargs["condition"]
                )
            )

        # ----------------------------
        # Status
        # ----------------------------

        if "status" in kwargs:

            asset.status = (
                AssetService._validate_status(
                    kwargs["status"]
                )
            )

        # ----------------------------
        # Location
        # ----------------------------

        if "location" in kwargs:

            location = kwargs["location"].strip()

            if len(location) < 2:
                raise ValidationError(
                    "Invalid location."
                )

            asset.location = location

        # ----------------------------
        # Department
        # ----------------------------

        if "department" in kwargs:

            asset.department = (
                AssetService._validate_department(
                    kwargs["department"]
                )
            )

        # ----------------------------
        # Remarks
        # ----------------------------

        if "remarks" in kwargs:

            remarks = kwargs["remarks"].strip()

            if len(remarks) > 1000:
                raise ValidationError(
                    "Remarks too long."
                )

            asset.remarks = remarks

        asset.full_clean()
        asset.save()

        return asset


    # --------------------------------------------------------
    # Change Asset Condition
    # --------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def change_condition(
        asset: Asset,
        new_condition: str,
        remarks: str = ""
    ):
        """
        Updates only asset condition.
        """

        if not isinstance(asset, Asset):
            raise ValidationError(
                "Invalid asset."
            )

        if asset.status == Asset.Status.DISPOSED:
            raise ValidationError(
                "Disposed assets cannot be modified."
            )

        new_condition = (
            AssetService._validate_condition(
                new_condition
            )
        )

        if asset.condition == new_condition:
            raise ValidationError(
                "Asset already has this condition."
            )

        asset.condition = new_condition

        if remarks:
            asset.remarks = remarks.strip()

        asset.full_clean()
        asset.save(
            update_fields=[
                "condition",
                "remarks",
                "updated_at",
            ]
        )

        return asset   
    
    from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import Employee
from assets.models import (
    Asset,
    ResourceBooking
)


class BookingService:

    # ======================================================
    # Helper Methods
    # ======================================================

    @staticmethod
    def _validate_employee(employee):

        if not isinstance(employee, Employee):
            raise ValidationError(
                "Invalid employee."
            )

        if not employee.is_active:
            raise ValidationError(
                "Inactive employee."
            )

        return employee


    @staticmethod
    def _validate_asset(asset):

        if not isinstance(asset, Asset):
            raise ValidationError(
                "Invalid asset."
            )

        return asset


    # ======================================================
    # Booking Conflict
    # ======================================================

    @staticmethod
    def check_booking_conflict(
        asset,
        start_datetime,
        end_datetime
    ):

        return ResourceBooking.objects.filter(

            asset=asset,

            status__in=[
                ResourceBooking.Status.PENDING,
                ResourceBooking.Status.APPROVED
            ]

        ).filter(

            Q(
                start_datetime__lt=end_datetime,
                end_datetime__gt=start_datetime
            )

        ).exists()


    # ======================================================
    # Create Booking
    # ======================================================

    @staticmethod
    @transaction.atomic
    def create_booking(

        *,
        asset,
        employee,
        purpose,
        start_datetime,
        end_datetime

    ):

        asset = BookingService._validate_asset(asset)

        employee = BookingService._validate_employee(
            employee
        )

        # ---------------------------------------

        if asset.status != Asset.Status.AVAILABLE:

            raise ValidationError(
                "Asset is not available for booking."
            )

        # ---------------------------------------

        if start_datetime >= end_datetime:

            raise ValidationError(
                "Invalid booking duration."
            )

        # ---------------------------------------

        if start_datetime < timezone.now():

            raise ValidationError(
                "Booking cannot start in past."
            )

        # ---------------------------------------

        if len(purpose.strip()) < 5:

            raise ValidationError(
                "Purpose is too short."
            )

        # ---------------------------------------

        duration = end_datetime - start_datetime

        if duration.total_seconds() <= 0:

            raise ValidationError(
                "Invalid booking duration."
            )

        # ---------------------------------------

        if BookingService.check_booking_conflict(

            asset,

            start_datetime,

            end_datetime

        ):

            raise ValidationError(
                "Time slot already booked."
            )

        booking = ResourceBooking.objects.create(

            asset=asset,

            employee=employee,

            purpose=purpose.strip(),

            start_datetime=start_datetime,

            end_datetime=end_datetime,

            status=ResourceBooking.Status.PENDING

        )

        return booking
    
        # ======================================================
    # Approve Booking
    # ======================================================

    @staticmethod
    @transaction.atomic
    def approve_booking(
        *,
        booking,
        approved_by
    ):
        """
        Approves a pending booking.

        Only Admin or Asset Manager can approve.
        """

        if not isinstance(booking, ResourceBooking):
            raise ValidationError(
                "Invalid booking."
            )

        approved_by = BookingService._validate_employee(
            approved_by
        )

        if approved_by.role not in [
            Employee.Role.ADMIN,
            Employee.Role.ASSET_MANAGER,
        ]:
            raise ValidationError(
                "You are not authorized to approve bookings."
            )

        if booking.status != ResourceBooking.Status.PENDING:
            raise ValidationError(
                "Only pending bookings can be approved."
            )

        if booking.end_datetime <= timezone.now():
            raise ValidationError(
                "Booking has already expired."
            )

        if BookingService.check_booking_conflict(
            booking.asset,
            booking.start_datetime,
            booking.end_datetime
        ):

            conflict = ResourceBooking.objects.filter(
                asset=booking.asset,
                status=ResourceBooking.Status.APPROVED
            ).exclude(
                pk=booking.pk
            ).filter(
                Q(
                    start_datetime__lt=booking.end_datetime,
                    end_datetime__gt=booking.start_datetime
                )
            )

            if conflict.exists():
                raise ValidationError(
                    "Booking conflicts with another approved booking."
                )

        booking.status = ResourceBooking.Status.APPROVED

        booking.full_clean()

        booking.save()

        return booking

    # ======================================================
    # Cancel Booking
    # ======================================================

    @staticmethod
    @transaction.atomic
    def cancel_booking(
        *,
        booking,
        cancelled_by,
        reason=""
    ):
        """
        Cancels a booking.

        Rules
        -----
        • Cannot cancel completed bookings.
        • Cannot cancel an already cancelled booking.
        """

        if not isinstance(booking, ResourceBooking):
            raise ValidationError(
                "Invalid booking."
            )

        cancelled_by = BookingService._validate_employee(
            cancelled_by
        )

        if booking.status == ResourceBooking.Status.CANCELLED:
            raise ValidationError(
                "Booking is already cancelled."
            )

        if hasattr(ResourceBooking.Status, "COMPLETED"):
            if booking.status == ResourceBooking.Status.COMPLETED:
                raise ValidationError(
                    "Completed bookings cannot be cancelled."
                )

        if (
            booking.employee != cancelled_by
            and cancelled_by.role not in [
                Employee.Role.ADMIN,
                Employee.Role.ASSET_MANAGER
            ]
        ):
            raise ValidationError(
                "You do not have permission to cancel this booking."
            )

        if timezone.now() >= booking.end_datetime:
            raise ValidationError(
                "Expired bookings cannot be cancelled."
            )

        if reason:

            reason = reason.strip()

            if len(reason) > 500:
                raise ValidationError(
                    "Reason exceeds maximum length."
                )

            booking.purpose += (
                f"\n\nCancellation Reason:\n{reason}"
            )

        booking.status = ResourceBooking.Status.CANCELLED

        booking.full_clean()

        booking.save()

        return booking
    
        # ======================================================
    # Complete Booking
    # ======================================================

    @staticmethod
    @transaction.atomic
    def complete_booking(
        *,
        booking
    ):
        """
        Marks an approved booking as completed.

        Can only be completed after the booking end time.
        """

        if not isinstance(booking, ResourceBooking):
            raise ValidationError(
                "Invalid booking."
            )

        if booking.status != ResourceBooking.Status.APPROVED:
            raise ValidationError(
                "Only approved bookings can be completed."
            )

        if timezone.now() < booking.end_datetime:
            raise ValidationError(
                "Booking duration has not ended yet."
            )

        if hasattr(ResourceBooking.Status, "COMPLETED"):
            booking.status = ResourceBooking.Status.COMPLETED

            booking.full_clean()

            booking.save()

        return booking


    # ======================================================
    # Booking History
    # ======================================================

    @staticmethod
    def booking_history(asset=None, employee=None):

        queryset = (
            ResourceBooking.objects
            .select_related(
                "asset",
                "employee"
            )
            .order_by(
                "-start_datetime"
            )
        )

        if asset:

            BookingService._validate_asset(asset)

            queryset = queryset.filter(
                asset=asset
            )

        if employee:

            BookingService._validate_employee(employee)

            queryset = queryset.filter(
                employee=employee
            )

        return queryset


    # ======================================================
    # Upcoming Bookings
    # ======================================================

    @staticmethod
    def upcoming_bookings():

        return (
            ResourceBooking.objects
            .select_related(
                "asset",
                "employee"
            )
            .filter(
                start_datetime__gt=timezone.now(),
                status__in=[
                    ResourceBooking.Status.PENDING,
                    ResourceBooking.Status.APPROVED
                ]
            )
            .order_by(
                "start_datetime"
            )
        )


    # ======================================================
    # Active Bookings
    # ======================================================

    @staticmethod
    def active_bookings():

        now = timezone.now()

        return (
            ResourceBooking.objects
            .select_related(
                "asset",
                "employee"
            )
            .filter(
                start_datetime__lte=now,
                end_datetime__gte=now,
                status=ResourceBooking.Status.APPROVED
            )
        )


    # ======================================================
    # Employee Bookings
    # ======================================================

    @staticmethod
    def employee_bookings(employee):

        employee = BookingService._validate_employee(
            employee
        )

        return (
            ResourceBooking.objects
            .select_related(
                "asset"
            )
            .filter(
                employee=employee
            )
            .order_by(
                "-start_datetime"
            )
        )


    # ======================================================
    # Asset Bookings
    # ======================================================

    @staticmethod
    def asset_bookings(asset):

        asset = BookingService._validate_asset(
            asset
        )

        return (
            ResourceBooking.objects
            .select_related(
                "employee"
            )
            .filter(
                asset=asset
            )
            .order_by(
                "-start_datetime"
            )
        )


    # ======================================================
    # Pending Bookings
    # ======================================================

    @staticmethod
    def pending_bookings():

        return (
            ResourceBooking.objects
            .select_related(
                "asset",
                "employee"
            )
            .filter(
                status=ResourceBooking.Status.PENDING
            )
            .order_by(
                "start_datetime"
            )
        )


    # ======================================================
    # Approved Bookings
    # ======================================================

    @staticmethod
    def approved_bookings():

        return (
            ResourceBooking.objects
            .select_related(
                "asset",
                "employee"
            )
            .filter(
                status=ResourceBooking.Status.APPROVED
            )
            .order_by(
                "start_datetime"
            )
        )
    
    from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import Employee
from assets.models import (
    Asset,
    MaintenanceRequest
)


class MaintenanceService:

    # =====================================================
    # Helper Methods
    # =====================================================

    @staticmethod
    def _validate_asset(asset):

        if not isinstance(asset, Asset):
            raise ValidationError(
                "Invalid asset."
            )

        return asset


    @staticmethod
    def _validate_employee(employee):

        if not isinstance(employee, Employee):
            raise ValidationError(
                "Invalid employee."
            )

        if not employee.is_active:
            raise ValidationError(
                "Employee is inactive."
            )

        return employee


    @staticmethod
    def has_open_request(asset):

        return MaintenanceRequest.objects.filter(

            asset=asset,

            status__in=[

                MaintenanceRequest.Status.PENDING,

                MaintenanceRequest.Status.APPROVED,

                MaintenanceRequest.Status.IN_PROGRESS

            ]

        ).exists()


    # =====================================================
    # Create Maintenance Request
    # =====================================================

    @staticmethod
    @transaction.atomic
    def create_request(

        *,

        asset,

        reported_by,

        issue,

        priority=MaintenanceRequest.Priority.MEDIUM

    ):

        asset = MaintenanceService._validate_asset(
            asset
        )

        reported_by = (
            MaintenanceService._validate_employee(
                reported_by
            )
        )

        # ------------------------------------------

        if asset.status == Asset.Status.DISPOSED:

            raise ValidationError(
                "Disposed asset cannot have maintenance requests."
            )

        # ------------------------------------------

        if asset.status == Asset.Status.RETIRED:

            raise ValidationError(
                "Retired asset cannot have maintenance requests."
            )

        # ------------------------------------------

        if MaintenanceService.has_open_request(
            asset
        ):

            raise ValidationError(
                "Maintenance request already exists."
            )

        # ------------------------------------------

        if not issue:

            raise ValidationError(
                "Issue description is required."
            )

        issue = issue.strip()

        if len(issue) < 10:

            raise ValidationError(
                "Issue description is too short."
            )

        if priority not in MaintenanceRequest.Priority.values:

            raise ValidationError(
                "Invalid priority."
            )

        request = MaintenanceRequest.objects.create(

            asset=asset,

            reported_by=reported_by,

            issue=issue,

            priority=priority,

            status=MaintenanceRequest.Status.PENDING

        )

        return request
    
        # =====================================================
    # Approve Maintenance Request
    # =====================================================

    @staticmethod
    @transaction.atomic
    def approve_request(
        *,
        request,
        approved_by
    ):
        """
        Approve a maintenance request.

        Rules
        -----
        • Only Admin or Asset Manager can approve.
        • Only Pending requests can be approved.
        • Asset moves to UNDER_MAINTENANCE.
        """

        if not isinstance(request, MaintenanceRequest):
            raise ValidationError(
                "Invalid maintenance request."
            )

        approved_by = (
            MaintenanceService._validate_employee(
                approved_by
            )
        )

        if approved_by.role not in [
            Employee.Role.ADMIN,
            Employee.Role.ASSET_MANAGER
        ]:
            raise ValidationError(
                "You are not authorized to approve maintenance requests."
            )

        if request.status != MaintenanceRequest.Status.PENDING:
            raise ValidationError(
                "Only pending requests can be approved."
            )

        asset = request.asset

        if asset.status == Asset.Status.DISPOSED:
            raise ValidationError(
                "Disposed assets cannot be maintained."
            )

        if asset.status == Asset.Status.RETIRED:
            raise ValidationError(
                "Retired assets cannot be maintained."
            )

        request.status = MaintenanceRequest.Status.APPROVED

        # Uncomment if fields are added
        # request.approved_by = approved_by
        # request.approved_on = timezone.now()

        request.full_clean()
        request.save()

        asset.status = Asset.Status.UNDER_MAINTENANCE

        asset.full_clean()

        asset.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        return request


    # =====================================================
    # Assign Employee
    # =====================================================

    @staticmethod
    @transaction.atomic
    def assign_employee(
        *,
        request,
        employee
    ):
        """
        Assign maintenance to an employee.

        Rules
        -----
        • Request must be APPROVED.
        • Assigned employee must be active.
        • Request moves to IN_PROGRESS.
        """

        if not isinstance(request, MaintenanceRequest):
            raise ValidationError(
                "Invalid maintenance request."
            )

        employee = (
            MaintenanceService._validate_employee(
                employee
            )
        )

        if request.status != MaintenanceRequest.Status.APPROVED:
            raise ValidationError(
                "Only approved requests can be assigned."
            )

        if request.assigned_to:
            raise ValidationError(
                "Maintenance request already assigned."
            )

        request.assigned_to = employee

        request.status = (
            MaintenanceRequest.Status.IN_PROGRESS
        )

        request.full_clean()

        request.save()

        return request


    # =====================================================
    # Helper Queries
    # =====================================================

    @staticmethod
    def pending_requests():

        return (
            MaintenanceRequest.objects
            .select_related(
                "asset",
                "reported_by"
            )
            .filter(
                status=MaintenanceRequest.Status.PENDING
            )
            .order_by(
                "-reported_on"
            )
        )


    @staticmethod
    def approved_requests():

        return (
            MaintenanceRequest.objects
            .select_related(
                "asset",
                "reported_by",
                "assigned_to"
            )
            .filter(
                status=MaintenanceRequest.Status.APPROVED
            )
        )


    @staticmethod
    def in_progress_requests():

        return (
            MaintenanceRequest.objects
            .select_related(
                "asset",
                "reported_by",
                "assigned_to"
            )
            .filter(
                status=MaintenanceRequest.Status.IN_PROGRESS
            )
        )
    
        # =====================================================
    # Resolve Maintenance Request
    # =====================================================

    @staticmethod
    @transaction.atomic
    def resolve_request(
        *,
        request,
        remarks=""
    ):
        """
        Resolves a maintenance request.

        Business Rules
        --------------
        • Request must be IN_PROGRESS.
        • Asset becomes AVAILABLE.
        • Request becomes RESOLVED.
        """

        if not isinstance(request, MaintenanceRequest):
            raise ValidationError(
                "Invalid maintenance request."
            )

        if request.status != MaintenanceRequest.Status.IN_PROGRESS:
            raise ValidationError(
                "Only requests in progress can be resolved."
            )

        asset = request.asset

        if remarks:

            remarks = remarks.strip()

            if len(remarks) > 1000:
                raise ValidationError(
                    "Remarks exceed maximum length."
                )

            request.remarks = remarks

        request.status = MaintenanceRequest.Status.RESOLVED

        request.resolved_on = timezone.now()

        request.full_clean()

        request.save()

        asset.status = Asset.Status.AVAILABLE

        asset.full_clean()

        asset.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        return request


    # =====================================================
    # Reject Maintenance Request
    # =====================================================

    @staticmethod
    @transaction.atomic
    def reject_request(
        *,
        request,
        rejected_by,
        remarks=""
    ):
        """
        Rejects a pending maintenance request.
        """

        if not isinstance(request, MaintenanceRequest):
            raise ValidationError(
                "Invalid maintenance request."
            )

        rejected_by = (
            MaintenanceService._validate_employee(
                rejected_by
            )
        )

        if rejected_by.role not in [
            Employee.Role.ADMIN,
            Employee.Role.ASSET_MANAGER
        ]:
            raise ValidationError(
                "You are not authorized to reject requests."
            )

        if request.status != MaintenanceRequest.Status.PENDING:
            raise ValidationError(
                "Only pending requests can be rejected."
            )

        request.status = MaintenanceRequest.Status.REJECTED

        if remarks:

            remarks = remarks.strip()

            if len(remarks) > 1000:
                raise ValidationError(
                    "Remarks exceed maximum length."
                )

            request.remarks = remarks

        request.full_clean()

        request.save()

        return request


    # =====================================================
    # Maintenance History
    # =====================================================

    @staticmethod
    def maintenance_history():

        return (
            MaintenanceRequest.objects
            .select_related(
                "asset",
                "reported_by",
                "assigned_to"
            )
            .order_by(
                "-reported_on"
            )
        )


    # =====================================================
    # Asset Maintenance History
    # =====================================================

    @staticmethod
    def asset_history(asset):

        asset = MaintenanceService._validate_asset(
            asset
        )

        return (
            MaintenanceRequest.objects
            .select_related(
                "reported_by",
                "assigned_to"
            )
            .filter(
                asset=asset
            )
            .order_by(
                "-reported_on"
            )
        )


    # =====================================================
    # Employee Maintenance History
    # =====================================================

    @staticmethod
    def employee_history(employee):

        employee = (
            MaintenanceService._validate_employee(
                employee
            )
        )

        return (
            MaintenanceRequest.objects
            .select_related(
                "asset"
            )
            .filter(
                assigned_to=employee
            )
            .order_by(
                "-reported_on"
            )
        )


    # =====================================================
    # Open Requests
    # =====================================================

    @staticmethod
    def open_requests():

        return (
            MaintenanceRequest.objects
            .select_related(
                "asset",
                "reported_by",
                "assigned_to"
            )
            .filter(
                status__in=[
                    MaintenanceRequest.Status.PENDING,
                    MaintenanceRequest.Status.APPROVED,
                    MaintenanceRequest.Status.IN_PROGRESS
                ]
            )
            .order_by(
                "-reported_on"
            )
        )
    
    from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import Employee, Department
from assets.models import (
    Asset,
    AssetAllocation,
    AssetTransfer
)

from .allocation_service import AllocationService


class TransferService:

    # =====================================================
    # Helper Validation Methods
    # =====================================================

    @staticmethod
    def _validate_employee(employee):

        if not isinstance(employee, Employee):
            raise ValidationError("Invalid employee.")

        if not employee.is_active:
            raise ValidationError("Inactive employee.")

        return employee

    @staticmethod
    def _validate_department(department):

        if not isinstance(department, Department):
            raise ValidationError("Invalid department.")

        return department

    @staticmethod
    def _validate_asset(asset):

        if not isinstance(asset, Asset):
            raise ValidationError("Invalid asset.")

        return asset

    @staticmethod
    def has_pending_transfer(asset):

        return AssetTransfer.objects.filter(
            asset=asset,
            status=AssetTransfer.Status.PENDING
        ).exists()

    # =====================================================
    # Request Transfer
    # =====================================================

    @staticmethod
    @transaction.atomic
    def request_transfer(
        *,
        asset,
        to_department,
        requested_by,
        reason,
        to_employee=None
    ):

        asset = TransferService._validate_asset(asset)

        requested_by = (
            TransferService._validate_employee(
                requested_by
            )
        )

        to_department = (
            TransferService._validate_department(
                to_department
            )
        )

        if to_employee:

            to_employee = (
                TransferService._validate_employee(
                    to_employee
                )
            )

            if to_employee.department != to_department:

                raise ValidationError(
                    "Employee does not belong to target department."
                )

        if asset.status != Asset.Status.ALLOCATED:

            raise ValidationError(
                "Only allocated assets can be transferred."
            )

        allocation = (
            AllocationService.get_current_allocation(asset)
        )

        if allocation is None:

            raise ValidationError(
                "No active allocation found."
            )

        if TransferService.has_pending_transfer(asset):

            raise ValidationError(
                "A transfer request already exists."
            )

        if allocation.department == to_department:

            raise ValidationError(
                "Asset already belongs to this department."
            )

        if not reason or len(reason.strip()) < 10:

            raise ValidationError(
                "Reason should contain at least 10 characters."
            )

        transfer = AssetTransfer.objects.create(

            allocation=allocation,

            asset=asset,

            from_department=allocation.department,

            to_department=to_department,

            from_employee=allocation.employee,

            to_employee=to_employee,

            requested_by=requested_by,

            reason=reason.strip(),

            status=AssetTransfer.Status.PENDING

        )

        return transfer
    

        # =====================================================
    # Approve Transfer
    # =====================================================

    @staticmethod
    @transaction.atomic
    def approve_transfer(
        *,
        transfer,
        approved_by
    ):
        """
        Approves a transfer request.

        Only Admin or Asset Manager can approve.
        """

        if not isinstance(transfer, AssetTransfer):
            raise ValidationError(
                "Invalid transfer request."
            )

        approved_by = (
            TransferService._validate_employee(
                approved_by
            )
        )

        if approved_by.role not in [
            Employee.Role.ADMIN,
            Employee.Role.ASSET_MANAGER
        ]:
            raise ValidationError(
                "You don't have permission to approve transfers."
            )

        if transfer.status != AssetTransfer.Status.PENDING:
            raise ValidationError(
                "Only pending transfers can be approved."
            )

        allocation = transfer.allocation

        if allocation.status != AssetAllocation.Status.ACTIVE:
            raise ValidationError(
                "Allocation is no longer active."
            )

        transfer.status = AssetTransfer.Status.APPROVED
        transfer.approved_by = approved_by
        transfer.approved_date = timezone.now()

        transfer.full_clean()
        transfer.save()

        return transfer


    # =====================================================
    # Reject Transfer
    # =====================================================

    @staticmethod
    @transaction.atomic
    def reject_transfer(
        *,
        transfer,
        approved_by,
        reason=""
    ):
        """
        Rejects a transfer request.
        """

        if not isinstance(transfer, AssetTransfer):
            raise ValidationError(
                "Invalid transfer request."
            )

        approved_by = (
            TransferService._validate_employee(
                approved_by
            )
        )

        if approved_by.role not in [
            Employee.Role.ADMIN,
            Employee.Role.ASSET_MANAGER
        ]:
            raise ValidationError(
                "You don't have permission to reject transfers."
            )

        if transfer.status != AssetTransfer.Status.PENDING:
            raise ValidationError(
                "Only pending transfers can be rejected."
            )

        if reason:

            reason = reason.strip()

            transfer.reason = (
                f"{transfer.reason}\n\n"
                f"Rejection Reason:\n{reason}"
            )

        transfer.status = AssetTransfer.Status.REJECTED

        transfer.approved_by = approved_by

        transfer.approved_date = timezone.now()

        transfer.full_clean()

        transfer.save()

        return transfer
    
        # =====================================================
    # Complete Transfer
    # =====================================================

    @staticmethod
    @transaction.atomic
    def complete_transfer(
        *,
        transfer
    ):
        """
        Completes an approved transfer.

        Workflow
        --------
        Old Allocation  -> Returned
        New Allocation  -> Active
        Asset           -> Department Updated
        Transfer        -> Completed
        """

        if not isinstance(transfer, AssetTransfer):
            raise ValidationError(
                "Invalid transfer."
            )

        if transfer.status != AssetTransfer.Status.APPROVED:
            raise ValidationError(
                "Only approved transfers can be completed."
            )

        allocation = transfer.allocation

        if allocation.status != AssetAllocation.Status.ACTIVE:
            raise ValidationError(
                "Original allocation is no longer active."
            )

        asset = transfer.asset

        # ----------------------------------------
        # Close Previous Allocation
        # ----------------------------------------

        allocation.status = AssetAllocation.Status.RETURNED
        allocation.returned_on = timezone.now().date()

        allocation.full_clean()
        allocation.save()

        # ----------------------------------------
        # Create New Allocation
        # ----------------------------------------

        new_allocation = AssetAllocation.objects.create(

            asset=asset,

            employee=transfer.to_employee,

            department=transfer.to_department,

            allocated_by=transfer.approved_by,

            remarks=f"Transfer from {transfer.from_department.name}",

            status=AssetAllocation.Status.ACTIVE

        )

        # ----------------------------------------
        # Update Asset
        # ----------------------------------------

        asset.department = transfer.to_department

        asset.status = Asset.Status.ALLOCATED

        asset.full_clean()

        asset.save(
            update_fields=[
                "department",
                "status",
                "updated_at",
            ]
        )

        # ----------------------------------------
        # Close Transfer
        # ----------------------------------------

        transfer.status = AssetTransfer.Status.COMPLETED

        transfer.completed_date = timezone.now()

        transfer.full_clean()

        transfer.save()

        return new_allocation

    # =====================================================
    # Pending Transfers
    # =====================================================

    @staticmethod
    def pending_transfers():

        return (
            AssetTransfer.objects
            .select_related(
                "asset",
                "requested_by",
                "from_department",
                "to_department"
            )
            .filter(
                status=AssetTransfer.Status.PENDING
            )
            .order_by(
                "-request_date"
            )
        )

    # =====================================================
    # Transfer History
    # =====================================================

    @staticmethod
    def transfer_history(asset):

        TransferService._validate_asset(asset)

        return (
            AssetTransfer.objects
            .select_related(
                "requested_by",
                "approved_by",
                "from_department",
                "to_department",
                "from_employee",
                "to_employee"
            )
            .filter(
                asset=asset
            )
            .order_by(
                "-request_date"
            )
        )

    # =====================================================
    # Helper Methods
    # =====================================================

    @staticmethod
    def approved_transfers():

        return (
            AssetTransfer.objects.filter(
                status=AssetTransfer.Status.APPROVED
            )
        )

    @staticmethod
    def completed_transfers():

        return (
            AssetTransfer.objects.filter(
                status=AssetTransfer.Status.COMPLETED
            )
        )

    @staticmethod
    def rejected_transfers():

        return (
            AssetTransfer.objects.filter(
                status=AssetTransfer.Status.REJECTED
            )
        )