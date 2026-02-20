from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Attendance, User


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'check_in', 'check_out', 'total_hours', 'status')
    list_filter = ('date', 'status')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    date_hierarchy = 'date'
    ordering = ('-date', 'user')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'status', 'created_at', 'is_staff')
    list_filter = ('role', 'status', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role', 'status', 'created_at')}),
    )
    readonly_fields = ('created_at',)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'status')}),
    )
