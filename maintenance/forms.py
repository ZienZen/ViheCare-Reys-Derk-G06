from django import forms
from django.utils import timezone

from vehicles.models import Vehicle

from .models import MaintenanceRecord, MaintenanceType, Reminder, add_months

REMIND_CHOICES = [
    ('', 'No reminder'),
    (1, '1 month'),
    (2, '2 months'),
    (3, '3 months'),
    (4, '4 months'),
    (6, '6 months'),
    (12, '12 months'),
    (24, '24 months'),
]


class MaintenanceRecordForm(forms.ModelForm):
    remind_after_months = forms.TypedChoiceField(
        label='Remind me again in',
        choices=REMIND_CHOICES,
        coerce=int,
        empty_value=None,
        required=False,
        help_text='VehiCare will remind you to check or change it after this long.',
    )
    odometer_km = forms.IntegerField(
        label='Odometer (km)',
        min_value=0,
        error_messages={'min_value': 'Odometer cannot be negative.', 'invalid': 'Enter a whole number.'},
        widget=forms.NumberInput(attrs={'placeholder': 'e.g. 48210', 'inputmode': 'numeric'}),
    )
    cost = forms.DecimalField(
        label='Cost (optional)',
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        error_messages={'min_value': 'Cost cannot be negative.', 'invalid': 'Enter a valid amount.'},
        widget=forms.NumberInput(attrs={'placeholder': 'e.g. 1800', 'step': '0.01'}),
    )

    class Meta:
        model = MaintenanceRecord
        fields = [
            'vehicle', 'maintenance_type', 'service_date', 'odometer_km', 'cost',
            'remind_after_months', 'notes',
        ]
        labels = {
            'maintenance_type': 'What was done',
            'service_date': 'Date of service',
            'notes': 'Notes (optional)',
        }
        widgets = {
            'service_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'notes': forms.TextInput(attrs={'placeholder': 'e.g. Fully synthetic 5W-30', 'maxlength': 255}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        # Owners can only pick their own vehicles (BR-06).
        self.fields['vehicle'].queryset = Vehicle.objects.filter(user=user)
        self.fields['vehicle'].empty_label = 'Choose a vehicle'
        self.fields['vehicle'].error_messages['required'] = 'Choose a vehicle.'
        self.fields['maintenance_type'].queryset = MaintenanceType.objects.all()
        self.fields['maintenance_type'].empty_label = 'Choose a service'
        self.fields['maintenance_type'].error_messages['required'] = 'Choose what was done.'
        self.fields['service_date'].error_messages['required'] = 'Enter the date of the service.'
        self.fields['service_date'].widget.attrs['max'] = timezone.localdate().isoformat()

    def clean_service_date(self):
        service_date = self.cleaned_data['service_date']
        if service_date > timezone.localdate():
            raise forms.ValidationError('Service date cannot be in the future.')  # BR-10
        return service_date

    def clean(self):
        cleaned = super().clean()
        service_date = cleaned.get('service_date')
        months = cleaned.get('remind_after_months')
        if service_date and months:
            due = add_months(service_date, months)
            existing = None
            if self.instance.pk:
                existing = Reminder.objects.filter(source_record=self.instance).first()
            unchanged = existing is not None and existing.due_date == due
            if due < timezone.localdate() and not unchanged:  # BR-12
                self.add_error(
                    'remind_after_months',
                    f'With that date the next reminder would be {due:%b %d, %Y}, which has already '
                    'passed. Pick a longer interval or choose "No reminder".',
                )
        return cleaned
