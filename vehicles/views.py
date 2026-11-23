from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import UserProfile

from .forms import VehicleForm
from .models import Vehicle

OWNER = UserProfile.Role.VEHICLE_OWNER
ADMIN = UserProfile.Role.ADMIN


def _own_vehicle(request, pk):
    """Fetch a vehicle only if it belongs to the logged-in owner (BR-06)."""
    return get_object_or_404(Vehicle, pk=pk, user=request.user)


@role_required(OWNER)
def vehicle_list(request):
    all_mine = Vehicle.objects.filter(user=request.user)
    vehicles = all_mine
    q = request.GET.get('q', '').strip()
    vtype = request.GET.get('type', '')
    if q:
        vehicles = vehicles.filter(
            Q(brand__icontains=q) | Q(model__icontains=q) | Q(plate_number__icontains=q)
        )
    if vtype in Vehicle.VehicleType.values:
        vehicles = vehicles.filter(vehicle_type=vtype)
    context = {
        'vehicles': vehicles,
        'total': all_mine.count(),
        'q': q,
        'vtype': vtype,
        'types': Vehicle.VehicleType.choices,
    }
    return render(request, 'vehicles/list.html', context)


@role_required(OWNER)
def vehicle_create(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST, user=request.user)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.user = request.user
            try:
                vehicle.save()
            except IntegrityError:
                form.add_error('plate_number', 'You already saved a vehicle with this plate number.')
            else:
                messages.success(request, f'{vehicle.brand} {vehicle.model} was added.')
                return redirect('vehicles:detail', pk=vehicle.pk)
        messages.error(request, 'Please fix the errors below.')
    else:
        form = VehicleForm(user=request.user)
    return render(request, 'vehicles/form.html', {'form': form, 'heading': 'Add a vehicle', 'submit': 'Save vehicle'})


@role_required(OWNER)
def vehicle_detail(request, pk):
    return render(request, 'vehicles/detail.html', {'vehicle': _own_vehicle(request, pk)})


@role_required(OWNER)
def vehicle_update(request, pk):
    vehicle = _own_vehicle(request, pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle, user=request.user)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                form.add_error('plate_number', 'You already saved a vehicle with this plate number.')
            else:
                messages.success(request, 'Vehicle updated.')
                return redirect('vehicles:detail', pk=vehicle.pk)
        messages.error(request, 'Please fix the errors below.')
    else:
        form = VehicleForm(instance=vehicle, user=request.user)
    return render(
        request,
        'vehicles/form.html',
        {'form': form, 'vehicle': vehicle, 'heading': 'Edit vehicle', 'submit': 'Save changes'},
    )


@role_required(OWNER)
def vehicle_delete(request, pk):
    """GET shows a confirmation page; only POST actually deletes (BR-09)."""
    vehicle = _own_vehicle(request, pk)
    if request.method == 'POST':
        label = f'{vehicle.brand} {vehicle.model}'
        vehicle.delete()
        messages.success(request, f'{label} was deleted.')
        return redirect('vehicles:list')
    return render(request, 'vehicles/confirm_delete.html', {'vehicle': vehicle})


@role_required(ADMIN)
def admin_vehicle_list(request):
    """Read-only overview of every vehicle for monitoring; admins cannot edit owners' data."""
    vehicles = Vehicle.objects.select_related('user', 'user__profile')
    q = request.GET.get('q', '').strip()
    if q:
        vehicles = vehicles.filter(
            Q(brand__icontains=q)
            | Q(model__icontains=q)
            | Q(plate_number__icontains=q)
            | Q(user__username__icontains=q)
            | Q(user__profile__full_name__icontains=q)
        )
    return render(request, 'vehicles/admin_list.html', {'vehicles': vehicles, 'q': q})
