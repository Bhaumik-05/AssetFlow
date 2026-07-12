from rest_framework import serializers
from .models import Employee, Department


# =====================================================
# Department Serializer
# =====================================================

class DepartmentSerializer(serializers.ModelSerializer):
    hod_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "code",
            "description",
            "hod",
            "hod_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "hod_name",
        ]

    def get_hod_name(self, obj):
        if obj.hod:
            return f"{obj.hod.first_name} {obj.hod.last_name}"
        return None


# =====================================================
# Employee Serializer
# =====================================================

class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source="department.name",
        read_only=True
    )

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "department",
            "department_name",
            "is_active",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "date_joined",
            "department_name",
        ]


# =====================================================
# Employee Create Serializer
# =====================================================

class EmployeeCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    employee_id = serializers.CharField(max_length=20)
    password = serializers.CharField(
        write_only=True,
        min_length=6
    )
    role = serializers.ChoiceField(
        choices=Employee.Role.choices,
        default=Employee.Role.EMPLOYEE
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        required=False,
        allow_null=True
    )


# =====================================================
# Employee Update Serializer
# =====================================================

class EmployeeUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        max_length=150,
        required=False
    )
    last_name = serializers.CharField(
        max_length=150,
        required=False
    )
    phone = serializers.CharField(
        max_length=15,
        required=False
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        required=False,
        allow_null=True
    )


# =====================================================
# Change Role Serializer
# =====================================================

class ChangeRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=Employee.Role.choices
    )


# =====================================================
# Assign Department Serializer
# =====================================================

class AssignDepartmentSerializer(serializers.Serializer):
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all()
    )


# =====================================================
# Department Create Serializer
# =====================================================

class DepartmentCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    code = serializers.CharField(max_length=10)
    description = serializers.CharField(
        required=False,
        allow_blank=True
    )


# =====================================================
# Department Update Serializer
# =====================================================

class DepartmentUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=100,
        required=False
    )
    code = serializers.CharField(
        max_length=10,
        required=False
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True
    )


# =====================================================
# Assign HOD Serializer
# =====================================================

class AssignHODSerializer(serializers.Serializer):
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(
            role=Employee.Role.HOD
        )
    )


from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()