from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        VEHICLE_OWNER = 'VEHICLE_OWNER', 'Vehicle Owner'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile'
    )
    full_name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VEHICLE_OWNER)

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN


def ensure_profile(user):
    """Return the user's profile, creating it if it is somehow missing."""
    role = UserProfile.Role.ADMIN if user.is_superuser else UserProfile.Role.VEHICLE_OWNER
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={'full_name': user.get_full_name() or user.username, 'role': role},
    )
    return profile
