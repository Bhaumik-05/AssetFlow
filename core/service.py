from .models import Notification, ActivityLog


def create_notification(employee, title, message):
    return Notification.objects.create(
        employee=employee,
        title=title,
        message=message
    )


def mark_notification_as_read(notification):
    notification.is_read = True
    notification.save(update_fields=["is_read"])


def log_activity(
    employee,
    module,
    action,
    object_id,
    ip_address=None,
):
    return ActivityLog.objects.create(
        employee=employee,
        module=module,
        action=action,
        object_id=object_id,
        ip_address=ip_address or "127.0.0.1",
    )