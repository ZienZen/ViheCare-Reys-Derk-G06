import calendar
from datetime import date, timedelta

from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from vehicles.models import Vehicle

DUE_SOON_DAYS = 30  # BR-13: reminders due within 30 days are highlighted


def add_months(start, months):
    """Add whole months to a date, clamping the day (Jan 31 + 1 month = Feb 28/29)."""
    index = start.month - 1 + months
    year = start.year + index // 12
    month = index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


class MaintenanceType(models.Model):
    """Fixed list of service types, e.g. Oil Change or Brake Pads."""

    type_name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ['type_name']

    def __str__(self):
        return self.type_name


class MaintenanceRecord(models.Model):
    """One service that was done on one vehicle (ERD: Vehicle 1 --- * MaintenanceRecord)."""

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.ForeignKey(
        MaintenanceType, on_delete=models.PROTECT, related_name='records'
    )
    service_date = models.DateField()
    odometer_km = models.PositiveIntegerField()
    cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    remind_after_months = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-service_date', '-id']

    def __str__(self):
        return f'{self.maintenance_type} on {self.service_date} ({self.vehicle.plate_number})'

    @property
    def next_due_date(self):
        if not self.remind_after_months:
            return None
        return add_months(self.service_date, self.remind_after_months)


class ReminderQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(vehicle__user=user)

    def pending(self):
        return self.filter(status=Reminder.Status.PENDING)

    def overdue(self):
        return self.pending().filter(due_date__lt=timezone.localdate())

    def due_soon(self):
        today = timezone.localdate()
        return self.pending().filter(
            due_date__gte=today, due_date__lte=today + timedelta(days=DUE_SOON_DAYS)
        )

    def needs_attention(self):
        """Overdue plus due within 30 days."""
        return self.pending().filter(due_date__lte=timezone.localdate() + timedelta(days=DUE_SOON_DAYS))


class Reminder(models.Model):
    """A pending or finished reminder to service a vehicle again."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        DONE = 'DONE', 'Done'

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='reminders')
    maintenance_type = models.ForeignKey(
        MaintenanceType, on_delete=models.PROTECT, related_name='reminders'
    )
    source_record = models.OneToOneField(
        MaintenanceRecord, on_delete=models.CASCADE, null=True, blank=True, related_name='reminder'
    )
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ReminderQuerySet.as_manager()

    class Meta:
        ordering = ['due_date']
        constraints = [
            # BR-12: a vehicle can have only one Pending reminder per maintenance type.
            models.UniqueConstraint(
                fields=['vehicle', 'maintenance_type'],
                condition=Q(status='PENDING'),
                name='one_pending_reminder_per_type',
            ),
        ]

    def __str__(self):
        return f'{self.maintenance_type} due {self.due_date} ({self.vehicle.plate_number})'

    @property
    def state(self):
        """CSS-friendly state: done, overdue, soon, or upcoming (BR-13)."""
        if self.status == self.Status.DONE:
            return 'done'
        today = timezone.localdate()
        if self.due_date < today:
            return 'overdue'
        if self.due_date <= today + timedelta(days=DUE_SOON_DAYS):
            return 'soon'
        return 'upcoming'

    @property
    def state_label(self):
        return {'done': 'Done', 'overdue': 'Overdue', 'soon': 'Due soon', 'upcoming': 'Upcoming'}[self.state]

    @property
    def days_left(self):
        return (self.due_date - timezone.localdate()).days


@transaction.atomic
def sync_reminder(record):
    """Create, update, or remove the reminder that belongs to a maintenance record."""
    due = record.next_due_date
    existing = Reminder.objects.filter(source_record=record).first()
    if due is None:
        if existing:
            existing.delete()
        return None

    others = Reminder.objects.filter(
        vehicle=record.vehicle, maintenance_type=record.maintenance_type, status=Reminder.Status.PENDING
    )
    if existing:
        others = others.exclude(pk=existing.pk)
    newer_exists = others.filter(source_record__service_date__gt=record.service_date).exists()
    if not newer_exists:
        # Servicing again replaces the older pending reminder for the same service (BR-12).
        others.filter(
            Q(source_record__isnull=True) | Q(source_record__service_date__lte=record.service_date)
        ).update(status=Reminder.Status.DONE)

    if existing is None:
        reminder = Reminder(source_record=record)
        reminder.status = Reminder.Status.DONE if newer_exists else Reminder.Status.PENDING
    else:
        reminder = existing
        if newer_exists:
            reminder.status = Reminder.Status.DONE
    reminder.vehicle = record.vehicle
    reminder.maintenance_type = record.maintenance_type
    reminder.due_date = due
    reminder.save()
    return reminder
