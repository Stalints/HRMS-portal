from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Attendance, HRProfile, LeaveCategory, LeaveRequest

# Get the actual Django User model
User = get_user_model()


# -------------------------
# ATTENDANCE ADMIN
# -------------------------
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'check_in', 'check_out', 'total_hours', 'status')
    list_filter = ('date', 'status')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    date_hierarchy = 'date'
    ordering = ('-date', 'user')


# -------------------------
# HR PROFILE ADMIN
# -------------------------
@admin.register(HRProfile)
class HRProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'status', 'created_at')
    list_filter = ('role', 'status')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


# -------------------------
# LEAVE CATEGORY ADMIN
# -------------------------
@admin.register(LeaveCategory)
class LeaveCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'days_per_year')


# -------------------------
# LEAVE REQUEST ADMIN
# -------------------------
@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'start_date', 'end_date', 'total_days', 'status', 'approved_by')
    list_filter = ('status', 'category')
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)
