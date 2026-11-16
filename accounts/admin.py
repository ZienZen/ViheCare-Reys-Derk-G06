from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'role', 'contact_number')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'full_name')
