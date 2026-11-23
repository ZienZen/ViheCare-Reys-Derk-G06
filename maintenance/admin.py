from django.contrib import admin

from .models import MaintenanceRecord, MaintenanceType, Reminder


@admin.register(MaintenanceType)
class MaintenanceTypeAdmin(admin.ModelAdmin):
    search_fields = ('type_name',)


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('maintenance_type', 'vehicle', 'service_date', 'odometer_km', 'cost')
    list_filter = ('maintenance_type',)
    search_fields = ('vehicle__plate_number', 'vehicle__user__username')


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('maintenance_type', 'vehicle', 'due_date', 'status')
    list_filter = ('status', 'maintenance_type')
