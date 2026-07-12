from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.contrib.auth.hashers import make_password

from .models import Employee, Department


# =====================================================
# Employee Service
# =====================================================

class EmployeeService:

    @staticmethod
    @transaction.atomic
    def create_employee(
        first_name,
        last_name,
        email,
        phone,
        employee_id,
        password,
        role=Employee.Role.EMPLOYEE,
        department=None
    ):

        # ---------- Validation ----------

        if not email:
            raise ValidationError("Email is required")

        if Employee.objects.filter(email=email).exists():
            raise ValidationError(
                "Employee with this email already exists"
            )

        if Employee.objects.filter(employee_id=employee_id).exists():
            raise ValidationError(
                "Employee ID already exists"
            )

        if Employee.objects.filter(phone=phone).exists():
            raise ValidationError(
                "Phone number already exists"
            )


        if role not in Employee.Role.values:
            raise ValidationError(
                "Invalid employee role"
            )


        # ---------- Department Validation ----------

        if role == Employee.Role.HOD and not department:
            raise ValidationError(
                "HOD must belong to a department"
            )


        employee = Employee.objects.create(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=email.lower().strip(),
            phone=phone,
            employee_id=employee_id,
            role=role,
            department=department,
            password=make_password(password)
        )

        return employee



    @staticmethod
    @transaction.atomic
    def update_employee(employee, data):

        allowed_fields = [
            "first_name",
            "last_name",
            "phone",
            "department"
        ]


        for field,value in data.items():

            if field not in allowed_fields:
                raise ValidationError(
                    f"{field} cannot be updated"
                )


            setattr(employee, field, value)


        employee.full_clean()
        employee.save()

        return employee



    @staticmethod
    @transaction.atomic
    def change_role(employee, new_role):


        if new_role not in Employee.Role.values:
            raise ValidationError(
                "Invalid role"
            )


        # HOD must have department

        if (
            new_role == Employee.Role.HOD
            and employee.department is None
        ):
            raise ValidationError(
                "HOD must belong to department"
            )


        employee.role = new_role
        employee.save()

        return employee



    @staticmethod
    @transaction.atomic
    def assign_department(employee, department):


        if not department:
            raise ValidationError(
                "Department is required"
            )


        employee.department = department


        if (
            employee.role == Employee.Role.HOD
            and department.hod
            and department.hod != employee
        ):
            raise ValidationError(
                "Department already has another HOD"
            )


        employee.save()

        return employee



    @staticmethod
    def activate_employee(employee):

        if employee.is_active:
            raise ValidationError(
                "Employee already active"
            )


        employee.is_active = True
        employee.save()

        return employee



    @staticmethod
    def deactivate_employee(employee):

        if not employee.is_active:
            raise ValidationError(
                "Employee already inactive"
            )


        employee.is_active = False
        employee.save()

        return employee



# =====================================================
# Department Service
# =====================================================


class DepartmentService:


    @staticmethod
    @transaction.atomic
    def create_department(
        name,
        code,
        description=""
    ):


        name = name.strip()
        code = code.upper().strip()


        if Department.objects.filter(
            name__iexact=name
        ).exists():

            raise ValidationError(
                "Department name already exists"
            )


        if Department.objects.filter(
            code__iexact=code
        ).exists():

            raise ValidationError(
                "Department code already exists"
            )


        department = Department.objects.create(
            name=name,
            code=code,
            description=description
        )


        return department



    @staticmethod
    @transaction.atomic
    def update_department(
        department,
        data
    ):


        allowed_fields=[
            "name",
            "code",
            "description"
        ]


        for field,value in data.items():


            if field not in allowed_fields:
                raise ValidationError(
                    f"{field} cannot be updated"
                )


            if field=="name":

                if Department.objects.filter(
                    name__iexact=value
                ).exclude(
                    id=department.id
                ).exists():

                    raise ValidationError(
                        "Department name already exists"
                    )


            if field=="code":

                value=value.upper()

                if Department.objects.filter(
                    code__iexact=value
                ).exclude(
                    id=department.id
                ).exists():

                    raise ValidationError(
                        "Department code already exists"
                    )


            setattr(
                department,
                field,
                value
            )


        department.full_clean()
        department.save()


        return department



    @staticmethod
    @transaction.atomic
    def delete_department(department):


        # Do not delete if employees exist

        if department.employees.filter(
            is_active=True
        ).exists():

            raise ValidationError(
                "Cannot delete department having active employees"
            )


        department.is_active=False
        department.save()


        return department



    @staticmethod
    @transaction.atomic
    def assign_hod(
        department,
        employee
    ):


        if employee.role != Employee.Role.HOD:

            raise ValidationError(
                "Employee role must be HOD"
            )


        if employee.department != department:

            raise ValidationError(
                "HOD must belong to same department"
            )


        if department.hod:

            raise ValidationError(
                "Department already has HOD"
            )


        department.hod = employee
        department.save()


        return department



    @staticmethod
    @transaction.atomic
    def remove_hod(department):


        if not department.hod:

            raise ValidationError(
                "No HOD assigned"
            )


        department.hod=None
        department.save()


        return department



    @staticmethod
    def get_department_assets(department):

        return department.assets.all()



    @staticmethod
    def get_department_employees(department):

        return department.employees.filter(
            is_active=True
        )