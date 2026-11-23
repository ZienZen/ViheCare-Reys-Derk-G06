from django.conf import settings
from django.db import models


class Vehicle(models.Model):
    """A car or motorcycle that belongs to one Vehicle Owner (ERD: User 1 --- * Vehicle)."""

    class VehicleType(models.TextChoices):
        CAR = 'CAR', 'Car'
        MOTORCYCLE = 'MOTORCYCLE', 'Motorcycle'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vehicles'
    )
    vehicle_type = models.CharField(max_length=12, choices=VehicleType.choices)
    brand = models.CharField(max_length=60)
    model = models.CharField(max_length=60)
    year = models.PositiveSmallIntegerField()
    plate_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['brand', 'model']
        constraints = [
            # BR-08: an owner cannot save two vehicles with the same plate number.
            models.UniqueConstraint(fields=['user', 'plate_number'], name='unique_plate_per_owner'),
        ]

    def __str__(self):
        return f'{self.year} {self.brand} {self.model} ({self.plate_number})'

    def save(self, *args, **kwargs):
        # Keep plates in one format so "abc 123" and "ABC  123" count as the same plate.
        self.plate_number = ' '.join(self.plate_number.upper().split())
        super().save(*args, **kwargs)
