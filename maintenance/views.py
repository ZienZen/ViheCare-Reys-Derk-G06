from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import UserProfile
from vehicles.models import Vehicle

from .forms import MaintenanceRecordForm
from .models import MaintenanceRecord, MaintenanceType, Reminder, sync_reminder

OWNER = UserProfile.Role.VEHICLE_OWNER
ADMIN = UserProfile.Role.ADMIN


def _own_record(request, pk):
    """A record is only reachable through the logged-in owner's vehicles (BR-06)."""
    return get_object_or_404(
        MaintenanceRecord.objects.select_related('vehicle', 'maintenance_type'),
        pk=pk,
        vehicle__user=request.user,
    )


def _saved_message(record, reminder, verb):
    text = f'{record.maintenance_type} {verb}.'
    if reminder and reminder.status == Reminder.Status.PENDING:
        text += f' You will be reminded on {reminder.due_date:%b %d, %Y}.'
    return text


@role_required(OWNER)
def record_list(request):
    all_mine = MaintenanceRecord.objects.filter(vehicle__user=request.user)
    records = all_mine.select_related('vehicle', 'maintenance_type', 'reminder')
    vehicle_id = request.GET.get('vehicle', '')
    type_id = request.GET.get('type', '')
    if vehicle_id.isdigit():
        records = records.filter(vehicle_id=vehicle_id)
    if type_id.isdigit():
        records = records.filter(maintenance_type_id=type_id)
    context = {
        'records': records,
        'total': all_mine.count(),
        'vehicles': Vehicle.objects.filter(user=request.user),
        'types': MaintenanceType.objects.all(),
        'vehicle_id': vehicle_id,
        'type_id': type_id,
    }
    return render(request, 'maintenance/list.html', context)


@role_required(OWNER)
def record_create(request):
    if not Vehicle.objects.filter(user=request.user).exists():
        messages.info(request, 'Add a vehicle first, then you can log its maintenance.')
        return redirect('vehicles:add')

    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                record = form.save()
                reminder = sync_reminder(record)
            messages.success(request, _saved_message(record, reminder, 'was saved'))
            return redirect('maintenance:detail', pk=record.pk)
        messages.error(request, 'Please fix the errors below.')
    else:
        initial = {}
        vehicle_id = request.GET.get('vehicle', '')
        type_id = request.GET.get('type', '')
        if vehicle_id.isdigit() and Vehicle.objects.filter(pk=vehicle_id, user=request.user).exists():
            initial['vehicle'] = vehicle_id
        if type_id.isdigit() and MaintenanceType.objects.filter(pk=type_id).exists():
            initial['maintenance_type'] = type_id
        form = MaintenanceRecordForm(user=request.user, initial=initial)
    return render(
        request,
        'maintenance/form.html',
        {'form': form, 'heading': 'Log a maintenance', 'submit': 'Save maintenance'},
    )


@role_required(OWNER)
def record_detail(request, pk):
    record = _own_record(request, pk)
    reminder = Reminder.objects.filter(source_record=record).first()
    return render(request, 'maintenance/detail.html', {'record': record, 'reminder': reminder})


@role_required(OWNER)
def record_update(request, pk):
    record = _own_record(request, pk)
    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST, instance=record, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                record = form.save()
                reminder = sync_reminder(record)
            messages.success(request, _saved_message(record, reminder, 'was updated'))
            return redirect('maintenance:detail', pk=record.pk)
        messages.error(request, 'Please fix the errors below.')
    else:
        form = MaintenanceRecordForm(instance=record, user=request.user)
    return render(
        request,
        'maintenance/form.html',
        {'form': form, 'record': record, 'heading': 'Edit maintenance', 'submit': 'Save changes'},
    )


@role_required(OWNER)
def record_delete(request, pk):
    """GET shows a confirmation page; only POST deletes (the reminder goes with it)."""
    record = _own_record(request, pk)
    if request.method == 'POST':
        label = str(record.maintenance_type)
        record.delete()
        messages.success(request, f'{label} record was deleted.')
        return redirect('maintenance:list')
    return render(request, 'maintenance/confirm_delete.html', {'record': record})


@role_required(OWNER)
def reminder_list(request):
    mine = Reminder.objects.for_user(request.user).select_related('vehicle', 'maintenance_type')
    context = {
        'pending': mine.pending(),
        'done': mine.filter(status=Reminder.Status.DONE).order_by('-due_date')[:10],
    }
    return render(request, 'maintenance/reminders.html', context)


@role_required(OWNER)
@require_POST
def reminder_done(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, vehicle__user=request.user)
    reminder.status = Reminder.Status.DONE
    reminder.save(update_fields=['status'])
    messages.success(request, f'{reminder.maintenance_type} reminder marked as done.')
    target = request.POST.get('next', '')
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return redirect(target)
    return redirect('maintenance:reminders')


@role_required(ADMIN)
def admin_record_list(request):
    """Read-only overview of all maintenance records for monitoring."""
    records = MaintenanceRecord.objects.select_related(
        'vehicle', 'vehicle__user', 'vehicle__user__profile', 'maintenance_type', 'reminder'
    )
    q = request.GET.get('q', '').strip()
    if q:
        records = records.filter(
            Q(maintenance_type__type_name__icontains=q)
            | Q(vehicle__plate_number__icontains=q)
            | Q(vehicle__brand__icontains=q)
            | Q(vehicle__model__icontains=q)
            | Q(vehicle__user__username__icontains=q)
            | Q(vehicle__user__profile__full_name__icontains=q)
        )
    return render(request, 'maintenance/admin_list.html', {'records': records, 'q': q})
