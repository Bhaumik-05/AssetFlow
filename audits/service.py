from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import Department, Employee
from assets.models import Asset
from .models import AuditCycle, AuditRecord


class AuditService:
    """
    Handles complete Audit Lifecycle.

    Flow

    Create Audit
            ↓
    Start Audit
            ↓
    Verify Assets
            ↓
    Identify Missing Assets
            ↓
    Complete Audit
            ↓
    Generate Report
    """

    # =====================================================
    # PRIVATE HELPERS
    # =====================================================

    @staticmethod
    def _validate_department(department):

        if department is None:
            raise ValidationError(
                "Department is required."
            )

        if not isinstance(department, Department):
            raise ValidationError(
                "Invalid department."
            )

        return department


    @staticmethod
    def _validate_employee(employee):

        if employee is None:
            raise ValidationError(
                "Employee is required."
            )

        if not isinstance(employee, Employee):
            raise ValidationError(
                "Invalid employee."
            )

        if not employee.is_active:
            raise ValidationError(
                "Employee account is inactive."
            )

        return employee


    @staticmethod
    def _validate_title(title):

        if not title:
            raise ValidationError(
                "Audit title is required."
            )

        title = title.strip()

        if len(title) < 5:
            raise ValidationError(
                "Audit title must contain at least 5 characters."
            )

        return title


    @staticmethod
    def _validate_dates(start_date, end_date):

        if not start_date or not end_date:
            raise ValidationError(
                "Start date and End date are required."
            )

        if start_date > end_date:
            raise ValidationError(
                "Start date cannot be after End date."
            )

        return start_date, end_date


    @staticmethod
    def _validate_audit_cycle(audit_cycle):

        if audit_cycle is None:
            raise ValidationError(
                "Audit cycle not found."
            )

        if not isinstance(audit_cycle, AuditCycle):
            raise ValidationError(
                "Invalid audit cycle."
            )

        return audit_cycle


    @staticmethod
    def _validate_audit_record(audit_record):

        if audit_record is None:
            raise ValidationError(
                "Audit record not found."
            )

        if not isinstance(audit_record, AuditRecord):
            raise ValidationError(
                "Invalid audit record."
            )

        return audit_record

    # =====================================================
    # CREATE AUDIT CYCLE
    # =====================================================

    @staticmethod
    @transaction.atomic
    def create_audit_cycle(
        *,
        title,
        department,
        start_date,
        end_date,
        conducted_by
    ):
        """
        Creates a new Audit Cycle.

        Rules
        -----
        ✔ Department must exist.
        ✔ Employee must be active.
        ✔ Valid dates.
        ✔ Duplicate title not allowed.
        ✔ Only one active audit per department.
        """

        title = AuditService._validate_title(title)

        department = AuditService._validate_department(
            department
        )

        conducted_by = AuditService._validate_employee(
            conducted_by
        )

        AuditService._validate_dates(
            start_date,
            end_date
        )

        # ----------------------------------------
        # Duplicate Title
        # ----------------------------------------

        if AuditCycle.objects.filter(
            title__iexact=title,
            department=department
        ).exists():

            raise ValidationError(
                "Audit title already exists for this department."
            )

        # ----------------------------------------
        # Existing Active Audit
        # ----------------------------------------

        if AuditCycle.objects.filter(
            department=department,
            status__in=[
                AuditCycle.Status.PLANNED,
                AuditCycle.Status.IN_PROGRESS
            ]
        ).exists():

            raise ValidationError(
                "Department already has an active audit."
            )

        # ----------------------------------------
        # Create Audit
        # ----------------------------------------

        audit = AuditCycle.objects.create(
            title=title,
            department=department,
            start_date=start_date,
            end_date=end_date,
            conducted_by=conducted_by,
            status=AuditCycle.Status.PLANNED
        )

        return audit
    
    # =====================================================
    # START AUDIT
    # =====================================================

    @staticmethod
    @transaction.atomic
    def start_audit(audit_cycle):
        """
        Starts an Audit Cycle.

        Rules
        -----
        ✔ Audit must exist.
        ✔ Audit must be in PLANNED state.
        ✔ Cannot start twice.
        ✔ Department must have assets.
        ✔ One AuditRecord per Asset.
        ✔ All records start with is_verified=False.
        ✔ Audit status becomes IN_PROGRESS.
        """

        audit_cycle = AuditService._validate_audit_cycle(
            audit_cycle
        )

        # ----------------------------------------
        # Status Validation
        # ----------------------------------------

        if audit_cycle.status != AuditCycle.Status.PLANNED:
            raise ValidationError(
                "Only planned audits can be started."
            )

        # ----------------------------------------
        # Prevent Duplicate Start
        # ----------------------------------------

        if AuditRecord.objects.filter(
            audit_cycle=audit_cycle
        ).exists():

            raise ValidationError(
                "Audit has already been started."
            )

        # ----------------------------------------
        # Department Assets
        # ----------------------------------------

        assets = Asset.objects.filter(
            department=audit_cycle.department
        ).order_by("asset_code")

        if not assets.exists():
            raise ValidationError(
                "No assets available for this department."
            )

        # ----------------------------------------
        # Create Audit Records
        # ----------------------------------------

        records = []

        for asset in assets:

            records.append(

                AuditRecord(

                    audit_cycle=audit_cycle,

                    asset=asset,

                    verified_by=audit_cycle.conducted_by,

                    condition=AuditRecord.Condition.GOOD,

                    status=AuditRecord.Status.VERIFIED,

                    is_verified=False,

                    remarks=""
                )
            )

        AuditRecord.objects.bulk_create(records)

        # ----------------------------------------
        # Update Audit Status
        # ----------------------------------------

        audit_cycle.status = AuditCycle.Status.IN_PROGRESS

        audit_cycle.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        return {
            "message": "Audit started successfully.",
            "audit_cycle": audit_cycle,
            "records_created": len(records)
        }
    # =====================================================
    # VERIFY ASSET
    # =====================================================

    @staticmethod
    @transaction.atomic
    def verify_asset(
        *,
        audit_record,
        verified_by,
        condition,
        status,
        remarks=""
    ):
        """
        Verify a single asset during an audit.

        Rules
        -----
        ✔ Audit must be IN_PROGRESS.
        ✔ AuditRecord must exist.
        ✔ Auditor must be active.
        ✔ Asset cannot be verified twice.
        ✔ Condition must be valid.
        ✔ Status must be valid.
        ✔ Missing asset -> Asset status becomes LOST.
        ✔ Damaged asset -> Asset status becomes UNDER_MAINTENANCE.
        ✔ Verified asset -> Only condition is updated.
        """

        audit_record = AuditService._validate_audit_record(
            audit_record
        )

        verified_by = AuditService._validate_employee(
            verified_by
        )

        audit_cycle = audit_record.audit_cycle

        # ----------------------------------------
        # Audit Status Validation
        # ----------------------------------------

        if audit_cycle.status != AuditCycle.Status.IN_PROGRESS:
            raise ValidationError(
                "Audit is not in progress."
            )

        # ----------------------------------------
        # Prevent Duplicate Verification
        # ----------------------------------------

        if audit_record.is_verified:
            raise ValidationError(
                "Asset has already been verified."
            )

        # ----------------------------------------
        # Validate Condition
        # ----------------------------------------

        if condition not in AuditRecord.Condition.values:
            raise ValidationError(
                "Invalid asset condition."
            )

        # ----------------------------------------
        # Validate Status
        # ----------------------------------------

        if status not in AuditRecord.Status.values:
            raise ValidationError(
                "Invalid audit status."
            )

        asset = audit_record.asset

        # ----------------------------------------
        # Update Audit Record
        # ----------------------------------------

        audit_record.verified_by = verified_by
        audit_record.condition = condition
        audit_record.status = status
        audit_record.remarks = remarks.strip()
        audit_record.is_verified = True

        audit_record.save(
            update_fields=[
                "verified_by",
                "condition",
                "status",
                "remarks",
                "is_verified",
                "updated_at"
            ]
        )

        # ----------------------------------------
        # Update Asset Condition
        # ----------------------------------------

        if condition == AuditRecord.Condition.NEW:
            asset.condition = Asset.Condition.NEW

        elif condition == AuditRecord.Condition.GOOD:
            asset.condition = Asset.Condition.GOOD

        elif condition == AuditRecord.Condition.FAIR:
            asset.condition = Asset.Condition.FAIR

        elif condition == AuditRecord.Condition.DAMAGED:
            asset.condition = Asset.Condition.DAMAGED

        # ----------------------------------------
        # Update Asset Status
        # ----------------------------------------

        if status == AuditRecord.Status.MISSING:

            asset.status = Asset.Status.LOST

        elif status == AuditRecord.Status.DAMAGED:

            asset.status = Asset.Status.UNDER_MAINTENANCE

        asset.save(
            update_fields=[
                "condition",
                "status",
                "updated_at"
            ]
        )

        return {
            "message": "Asset verified successfully.",
            "asset": asset,
            "audit_record": audit_record
        }
    
    # =====================================================
    # IDENTIFY MISSING ASSETS
    # =====================================================

    @staticmethod
    @transaction.atomic
    def identify_missing_assets(audit_cycle):
        """
        Identifies all assets that were not verified
        during the audit.

        Rules
        -----
        ✔ Audit must exist.
        ✔ Audit must be IN_PROGRESS.
        ✔ Only unverified assets are marked missing.
        ✔ Asset status becomes LOST.
        ✔ AuditRecord status becomes MISSING.
        ✔ is_verified becomes True.
        """

        audit_cycle = AuditService._validate_audit_cycle(
            audit_cycle
        )

        # ----------------------------------------
        # Audit Status Validation
        # ----------------------------------------

        if audit_cycle.status != AuditCycle.Status.IN_PROGRESS:
            raise ValidationError(
                "Audit must be in progress."
            )

        # ----------------------------------------
        # Fetch Unverified Records
        # ----------------------------------------

        missing_records = AuditRecord.objects.filter(
            audit_cycle=audit_cycle,
            is_verified=False
        ).select_related("asset")

        updated = 0

        # ----------------------------------------
        # Mark Missing
        # ----------------------------------------

        for record in missing_records:

            record.status = AuditRecord.Status.MISSING
            record.is_verified = True
            record.remarks = "Automatically marked missing."

            record.save(
                update_fields=[
                    "status",
                    "is_verified",
                    "remarks",
                    "updated_at"
                ]
            )

            asset = record.asset

            asset.status = Asset.Status.LOST

            asset.save(
                update_fields=[
                    "status",
                    "updated_at"
                ]
            )

            updated += 1

        return {
            "message": "Missing assets identified successfully.",
            "missing_assets": updated
        }

    # =====================================================
    # COMPLETE AUDIT
    # =====================================================

    @staticmethod
    @transaction.atomic
    def complete_audit(audit_cycle):
        """
        Completes an audit cycle.

        Rules
        -----
        ✔ Audit must exist.
        ✔ Audit must be IN_PROGRESS.
        ✔ Every AuditRecord must be verified.
        ✔ Audit status becomes COMPLETED.
        """

        audit_cycle = AuditService._validate_audit_cycle(
            audit_cycle
        )

        # ----------------------------------------
        # Audit Status Validation
        # ----------------------------------------

        if audit_cycle.status != AuditCycle.Status.IN_PROGRESS:
            raise ValidationError(
                "Only an active audit can be completed."
            )

        # ----------------------------------------
        # Check Pending Verification
        # ----------------------------------------

        pending_records = AuditRecord.objects.filter(
            audit_cycle=audit_cycle,
            is_verified=False
        )

        if pending_records.exists():

            raise ValidationError(
                "All assets must be verified before completing the audit."
            )

        # ----------------------------------------
        # Complete Audit
        # ----------------------------------------

        audit_cycle.status = AuditCycle.Status.COMPLETED

        audit_cycle.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        return {
            "message": "Audit completed successfully.",
            "audit_cycle": audit_cycle
        }
    
    # =====================================================
    # GENERATE AUDIT REPORT
    # =====================================================

    @staticmethod
    def generate_audit_report(audit_cycle):
        """
        Generates an audit summary.

        Rules
        -----
        ✔ Audit must exist.
        ✔ Returns summary statistics.
        ✔ Returns asset-wise details.
        """

        audit_cycle = AuditService._validate_audit_cycle(
            audit_cycle
        )

        records = AuditRecord.objects.filter(
            audit_cycle=audit_cycle
        ).select_related(
            "asset",
            "verified_by"
        )

        total_assets = records.count()

        verified_assets = records.filter(
            status=AuditRecord.Status.VERIFIED
        ).count()

        damaged_assets = records.filter(
            status=AuditRecord.Status.DAMAGED
        ).count()

        missing_assets = records.filter(
            status=AuditRecord.Status.MISSING
        ).count()

        verification_percentage = 0

        if total_assets > 0:

            verification_percentage = round(
                (
                    records.filter(
                        is_verified=True
                    ).count()
                    / total_assets
                ) * 100,
                2
            )

        asset_details = []

        for record in records:

            asset_details.append({

                "asset_code": record.asset.asset_code,

                "asset_name": record.asset.name,

                "condition": record.condition,

                "status": record.status,

                "verified": record.is_verified,

                "verified_by": (
                    str(record.verified_by)
                    if record.verified_by
                    else None
                ),

                "remarks": record.remarks,

                "verified_on": record.verified_on

            })

        return {

            "audit_title": audit_cycle.title,

            "department": audit_cycle.department.name,

            "conducted_by": str(
                audit_cycle.conducted_by
            ),

            "start_date": audit_cycle.start_date,

            "end_date": audit_cycle.end_date,

            "audit_status": audit_cycle.status,

            "summary": {

                "total_assets": total_assets,

                "verified_assets": verified_assets,

                "damaged_assets": damaged_assets,

                "missing_assets": missing_assets,

                "verification_percentage": verification_percentage

            },

            "assets": asset_details
        }