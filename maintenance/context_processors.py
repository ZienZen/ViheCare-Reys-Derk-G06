from .models import Reminder


def reminder_badge(request):
    """Number of reminders that are overdue or due within 30 days, for the owner's nav."""
    user = request.user
    if not user.is_authenticated:
        return {}
    profile = getattr(user, 'profile', None)
    if profile is None or profile.role != 'VEHICLE_OWNER':
        return {}
    return {'reminder_attention_count': Reminder.objects.for_user(user).needs_attention().count()}
