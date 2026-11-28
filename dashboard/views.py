from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.decorators import role_required
from accounts.models import UserProfile, ensure_profile
from maintenance.models import MaintenanceRecord, Reminder
from vehicles.models import Vehicle

User = get_user_model()


@login_required
def home(request):
    """Send each user to the dashboard for their role."""
    if ensure_profile(request.user).role == UserProfile.Role.ADMIN:
        return redirect('dashboard:admin')
    return redirect('dashboard:owner')


@role_required(UserProfile.Role.ADMIN)
def admin_dashboard(request):
    profiles = UserProfile.objects.select_related('user').order_by('-user__date_joined')
    context = {
        'total_users': profiles.count(),
        'owner_count': profiles.filter(role=UserProfile.Role.VEHICLE_OWNER).count(),
        'admin_count': profiles.filter(role=UserProfile.Role.ADMIN).count(),
        'recent_profiles': profiles[:10],
        'vehicle_count': Vehicle.objects.count(),
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@role_required(UserProfile.Role.VEHICLE_OWNER)
def owner_dashboard(request):
    vehicles = Vehicle.objects.filter(user=request.user)
    records = MaintenanceRecord.objects.filter(vehicle__user=request.user)
    attention = Reminder.objects.for_user(request.user).needs_attention()
    context = {
        'profile': ensure_profile(request.user),
        'vehicle_count': vehicles.count(),
        'recent_vehicles': vehicles.order_by('-created_at')[:5],
        'maintenance_count': records.count(),
        'recent_records': records.select_related('vehicle', 'maintenance_type').order_by('-service_date', '-id')[:5],
        'reminder_count': attention.count(),
        'recent_reminders': attention.select_related('vehicle', 'maintenance_type')[:5],
    }
    return render(request, 'dashboard/owner_dashboard.html', context)


def landing(request):
    """Public home page; signed-in users go straight to their dashboard."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return render(request, 'landing.html')
