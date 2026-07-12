from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout

from accounts.models import Employee, Department
from assets.models import Asset, AssetCategory, AssetAllocation, AssetTransfer, MaintenanceRequest, ResourceBooking
from audits.models import AuditCycle, AuditRecord
from core.models import Notification, ActivityLog
from core.dashboard_service import DashboardService
from core.report_service import ReportService


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Welcome back!')
            return HttpResponseRedirect(reverse('dashboard'))
        messages.error(request, 'Invalid credentials.')
    return render(request, 'authentication/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return HttpResponseRedirect(reverse('login_view'))


@login_required(login_url='login_view')
def dashboard_view(request):
    if request.user.role == Employee.Role.ADMIN:
        dashboard = DashboardService.admin_dashboard()
    elif request.user.role == Employee.Role.ASSET_MANAGER:
        dashboard = DashboardService.asset_manager_dashboard()
    elif request.user.role == Employee.Role.HOD:
        dashboard = DashboardService.hod_dashboard(request.user)
    else:
        dashboard = DashboardService.employee_dashboard(request.user)

    context = {'dashboard': dashboard, 'breadcrumb_title': 'Dashboard'}
    return render(request, 'dashboard/dashboard.html', context)


@login_required(login_url='login_view')
def employees_view(request):
    employees = Employee.objects.select_related('department').all()
    context = {'employees': employees, 'breadcrumb_title': 'Employees'}
    return render(request, 'accounts/employees.html', context)


@login_required(login_url='login_view')
def departments_view(request):
    departments = Department.objects.all()
    context = {'departments': departments, 'breadcrumb_title': 'Departments'}
    return render(request, 'accounts/departments.html', context)


@login_required(login_url='login_view')
def assets_view(request):
    assets = Asset.objects.select_related('category', 'department').all()
    context = {'assets': assets, 'breadcrumb_title': 'Assets'}
    return render(request, 'assets/assets.html', context)


@login_required(login_url='login_view')
def categories_view(request):
    categories = AssetCategory.objects.all()
    context = {'categories': categories, 'breadcrumb_title': 'Categories'}
    return render(request, 'assets/categories.html', context)


@login_required(login_url='login_view')
def allocations_view(request):
    allocations = AssetAllocation.objects.select_related('asset', 'employee', 'department', 'allocated_by').all()
    context = {'allocations': allocations, 'breadcrumb_title': 'Allocations'}
    return render(request, 'assets/allocations.html', context)


@login_required(login_url='login_view')
def transfers_view(request):
    transfers = AssetTransfer.objects.select_related('asset', 'from_department', 'to_department', 'requested_by').all()
    context = {'transfers': transfers, 'breadcrumb_title': 'Transfers'}
    return render(request, 'assets/transfers.html', context)


@login_required(login_url='login_view')
def maintenance_view(request):
    maintenance_requests = MaintenanceRequest.objects.select_related('asset', 'reported_by', 'assigned_to').all()
    context = {'maintenance_requests': maintenance_requests, 'breadcrumb_title': 'Maintenance'}
    return render(request, 'assets/maintenance.html', context)


@login_required(login_url='login_view')
def bookings_view(request):
    bookings = ResourceBooking.objects.select_related('asset', 'employee').all()
    context = {'bookings': bookings, 'breadcrumb_title': 'Bookings'}
    return render(request, 'assets/bookings.html', context)


@login_required(login_url='login_view')
def audit_cycles_view(request):
    audit_cycles = AuditCycle.objects.select_related('department', 'conducted_by').all()
    context = {'audit_cycles': audit_cycles, 'breadcrumb_title': 'Audit Cycles'}
    return render(request, 'audits/audit_cycles.html', context)


@login_required(login_url='login_view')
def audit_records_view(request):
    audit_records = AuditRecord.objects.select_related('audit_cycle', 'asset', 'verified_by').all()
    context = {'audit_records': audit_records, 'breadcrumb_title': 'Audit Records'}
    return render(request, 'audits/audit_records.html', context)


@login_required(login_url='login_view')
def notifications_view(request):
    notifications = Notification.objects.filter(employee=request.user).all()
    context = {'notifications': notifications, 'breadcrumb_title': 'Notifications'}
    return render(request, 'notifications/notifications.html', context)


@login_required(login_url='login_view')
def activity_logs_view(request):
    activity_logs = ActivityLog.objects.select_related('employee').all()
    context = {'activity_logs': activity_logs, 'breadcrumb_title': 'Activity Logs'}
    return render(request, 'activity_logs/activity_logs.html', context)


@login_required(login_url='login_view')
def reports_view(request):
    report_type = request.GET.get('type', 'assets')
    if report_type == 'assets':
        report_data = ReportService.asset_utilization()
    elif report_type == 'departments':
        report_data = ReportService.department_asset_report()
    elif report_type == 'maintenance':
        report_data = ReportService.maintenance_statistics()
    elif report_type == 'bookings':
        report_data = ReportService.booking_statistics()
    elif report_type == 'transfers':
        report_data = ReportService.transfer_statistics()
    elif report_type == 'audits':
        report_data = ReportService.audit_statistics()
    else:
        report_data = ReportService.asset_utilization()

    context = {'report_data': report_data, 'breadcrumb_title': 'Reports'}
    return render(request, 'reports/reports.html', context)
