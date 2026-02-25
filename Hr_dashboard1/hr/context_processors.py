from .models import Notification


def navbar_notifications(request):
    try:
        unread_count = Notification.objects.filter(is_read=False).count()
    except Exception:
        unread_count = 0
    return {"navbar_unread_notifications": unread_count}

