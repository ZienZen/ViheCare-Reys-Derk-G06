from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile, ensure_profile

User = get_user_model()


class RegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField(max_length=254)

    field_order = ['full_name', 'username', 'email', 'password1', 'password2']

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.save()  # signal creates a Vehicle Owner profile
        profile = ensure_profile(user)
        profile.full_name = self.cleaned_data['full_name'].strip()
        profile.save()
        return user


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(max_length=254)

    class Meta:
        model = UserProfile
        # "role" is deliberately not editable here.
        fields = ['full_name', 'email', 'contact_number', 'profile_photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].initial = self.instance.user.email

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        taken = User.objects.filter(email__iexact=email).exclude(pk=self.instance.user_id)
        if taken.exists():
            raise forms.ValidationError('This email is already used by another account.')
        return email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        user = profile.user
        user.email = self.cleaned_data['email']
        user.save(update_fields=['email'])
        return profile
