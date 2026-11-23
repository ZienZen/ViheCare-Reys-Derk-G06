import re
from datetime import date

from django import forms
from django.db import IntegrityError  # noqa: F401  (used by views)

from .models import Vehicle

PLATE_RE = re.compile(r'^[A-Z0-9][A-Z0-9 \-]{1,14}$')
MIN_YEAR = 1900


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['vehicle_type', 'brand', 'model', 'year', 'plate_number']
        labels = {'vehicle_type': 'Vehicle type', 'plate_number': 'Plate number'}
        widgets = {
            'brand': forms.TextInput(attrs={'placeholder': 'e.g. Toyota', 'maxlength': 60}),
            'model': forms.TextInput(attrs={'placeholder': 'e.g. Vios', 'maxlength': 60}),
            'year': forms.NumberInput(attrs={'placeholder': 'e.g. 2020', 'inputmode': 'numeric'}),
            'plate_number': forms.TextInput(attrs={'placeholder': 'e.g. ABC 1234', 'maxlength': 15}),
        }
        help_texts = {
            'plate_number': 'Letters, numbers, spaces, and hyphens. Each plate can be saved once.',
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['vehicle_type'].choices = [('', 'Choose a type')] + list(Vehicle.VehicleType.choices)
        self.fields['vehicle_type'].error_messages['required'] = 'Choose Car or Motorcycle.'

    def clean_brand(self):
        brand = ' '.join(self.cleaned_data['brand'].split())
        if not brand:
            raise forms.ValidationError('Brand is required.')
        return brand

    def clean_model(self):
        model = ' '.join(self.cleaned_data['model'].split())
        if not model:
            raise forms.ValidationError('Model is required.')
        return model

    def clean_year(self):
        year = self.cleaned_data['year']
        latest = date.today().year + 1  # allow next year's models
        if year < MIN_YEAR or year > latest:
            raise forms.ValidationError(f'Enter a year between {MIN_YEAR} and {latest}.')
        return year

    def clean_plate_number(self):
        plate = ' '.join(self.cleaned_data['plate_number'].upper().split())
        if not PLATE_RE.match(plate):
            raise forms.ValidationError(
                'Use 2 to 15 characters: letters, numbers, spaces, or hyphens only.'
            )
        duplicates = Vehicle.objects.filter(user=self.user, plate_number=plate)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError('You already saved a vehicle with this plate number.')
        return plate
