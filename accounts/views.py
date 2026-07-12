from django.shortcuts import render

# Create your views here.
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Employee, Department
from .serializers import (
    EmployeeSerializer,
    EmployeeCreateSerializer,
    EmployeeUpdateSerializer,
    ChangeRoleSerializer,
    AssignDepartmentSerializer,
)

from .service import EmployeeService


# =====================================================
# Employee List & Create
# =====================================================

class EmployeeListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employees = Employee.objects.all()
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EmployeeCreateSerializer(data=request.data)

        if serializer.is_valid():
            try:
                employee = EmployeeService.create_employee(
                    first_name=serializer.validated_data["first_name"],
                    last_name=serializer.validated_data["last_name"],
                    email=serializer.validated_data["email"],
                    phone=serializer.validated_data["phone"],
                    employee_id=serializer.validated_data["employee_id"],
                    password=serializer.validated_data["password"],
                    role=serializer.validated_data.get(
                        "role",
                        Employee.Role.EMPLOYEE
                    ),
                    department=serializer.validated_data.get("department"),
                )

                return Response(
                    EmployeeSerializer(employee).data,
                    status=status.HTTP_201_CREATED,
                )

            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        serializer = EmployeeSerializer(employee)
        return Response(serializer.data)

    def put(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)

        serializer = EmployeeUpdateSerializer(
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            try:
                employee = EmployeeService.update_employee(
                    employee,
                    serializer.validated_data
                )

                return Response(
                    EmployeeSerializer(employee).data
                )

            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class ChangeEmployeeRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        employee = get_object_or_404(Employee, pk=pk)

        serializer = ChangeRoleSerializer(
            data=request.data
        )

        if serializer.is_valid():

            try:
                employee = EmployeeService.change_role(
                    employee,
                    serializer.validated_data["role"],
                )

                return Response(
                    EmployeeSerializer(employee).data
                )

            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class AssignDepartmentView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        employee = get_object_or_404(Employee, pk=pk)

        serializer = AssignDepartmentSerializer(
            data=request.data
        )

        if serializer.is_valid():

            try:
                employee = EmployeeService.assign_department(
                    employee,
                    serializer.validated_data["department"],
                )

                return Response(
                    EmployeeSerializer(employee).data
                )

            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class ActivateEmployeeView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        employee = get_object_or_404(Employee, pk=pk)

        try:
            employee = EmployeeService.activate_employee(employee)

            return Response(
                EmployeeSerializer(employee).data
            )

        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

class DeactivateEmployeeView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        employee = get_object_or_404(Employee, pk=pk)

        try:
            employee = EmployeeService.deactivate_employee(employee)

            return Response(
                EmployeeSerializer(employee).data
            )

        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

from .serializers import (
    DepartmentSerializer,
    DepartmentCreateSerializer,
    DepartmentUpdateSerializer,
    AssignHODSerializer,
)

from .service import DepartmentService

# =====================================================
# Department List & Create
# =====================================================

class DepartmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DepartmentCreateSerializer(data=request.data)

        if serializer.is_valid():
            try:
                department = DepartmentService.create_department(
                    name=serializer.validated_data["name"],
                    code=serializer.validated_data["code"],
                    description=serializer.validated_data.get(
                        "description", ""
                    ),
                )

                return Response(
                    DepartmentSerializer(department).data,
                    status=status.HTTP_201_CREATED,
                )

            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

# =====================================================
# Department Detail
# =====================================================

class DepartmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        department = get_object_or_404(Department, pk=pk)

        serializer = DepartmentSerializer(department)

        return Response(serializer.data)

    def put(self, request, pk):
        department = get_object_or_404(Department, pk=pk)

        serializer = DepartmentUpdateSerializer(
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            try:

                department = DepartmentService.update_department(
                    department,
                    serializer.validated_data
                )

                return Response(
                    DepartmentSerializer(department).data
                )

            except ValidationError as e:

                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):

        department = get_object_or_404(
            Department,
            pk=pk
        )

        try:

            DepartmentService.delete_department(
                department
            )

            return Response(
                {"message": "Department deleted successfully"},
                status=status.HTTP_200_OK
            )

        except ValidationError as e:

            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

# =====================================================
# Assign HOD
# =====================================================

class AssignHODView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        department = get_object_or_404(
            Department,
            pk=pk
        )

        serializer = AssignHODSerializer(
            data=request.data
        )

        if serializer.is_valid():

            try:

                department = DepartmentService.assign_hod(
                    department,
                    serializer.validated_data["employee"]
                )

                return Response(
                    DepartmentSerializer(department).data
                )

            except ValidationError as e:

                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

# =====================================================
# Remove HOD
# =====================================================

class RemoveHODView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        department = get_object_or_404(
            Department,
            pk=pk
        )

        try:

            department = DepartmentService.remove_hod(
                department
            )

            return Response(
                DepartmentSerializer(department).data
            )

        except ValidationError as e:

            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

# =====================================================
# Department Employees
# =====================================================

class DepartmentEmployeesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        department = get_object_or_404(
            Department,
            pk=pk
        )

        employees = DepartmentService.get_department_employees(
            department
        )

        serializer = EmployeeSerializer(
            employees,
            many=True
        )

        return Response(serializer.data)

# =====================================================
# Department Assets
# =====================================================

class DepartmentAssetsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        department = get_object_or_404(
            Department,
            pk=pk
        )

        assets = DepartmentService.get_department_assets(
            department
        )

        data = []

        for asset in assets:
            data.append({
                "id": asset.id,
                "asset_name": getattr(asset, "asset_name", ""),
                "asset_code": getattr(asset, "asset_code", ""),
                "status": getattr(asset, "status", ""),
            })

        return Response(data)


