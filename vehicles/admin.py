from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'brand', 'model', 'year', 'vehicle_type', 'user')
    list_filter = ('vehicle_type',)
    search_fields = ('plate_number', 'brand', 'model', 'user__username')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
