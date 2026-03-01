from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LeaveRequest, Notification, NotificationType

@receiver(post_save, sender=LeaveRequest)
def notify_leave_status(sender, instance, created, **kwargs):
    # We only want to notify on updates, not on creation
    if not created and instance.status in ['Approved', 'Rejected']:
        Notification.objects.create(
            user=instance.user,
            title=f"Leave Request {instance.status}",
            message=f"Your leave request for {instance.start_date} to {instance.end_date} has been {instance.status.lower()}.",
            type=NotificationType.LEAVE
        )
