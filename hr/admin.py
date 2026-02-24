from django.contrib import admin
from .models import (
    Attendance,
    LeaveCategory,
    LeaveRequest,
    Announcement,
    Project,
    Task,
    Client,
    Team,
    Payroll,
    Invoice,
    Payment,
    Ticket,
    TicketComment,
    Event,
    Note,
    TimelinePost,
    TimelineComment,
    PersonalTask,
)


# -------------------------
# ATTENDANCE ADMIN
# -------------------------
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "check_in", "check_out", "total_hours", "status")
    list_filter = ("date", "status")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    date_hierarchy = "date"
    ordering = ("-date", "user")


# -------------------------
# LEAVE CATEGORY ADMIN
# -------------------------
@admin.register(LeaveCategory)
class LeaveCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "days_per_year")


# -------------------------
# LEAVE REQUEST ADMIN
# -------------------------
@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "start_date", "end_date", "total_days", "status", "approved_by")
    list_filter = ("status", "category")
    search_fields = ("user__username", "user__email")
    ordering = ("-created_at",)


# -------------------------
# ANNOUNCEMENTS ADMIN
# -------------------------
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "publish_date", "status", "created_by", "created_at")
    list_filter = ("status", "publish_date")
    search_fields = ("title", "message", "created_by__username", "created_by__email")
    ordering = ("-publish_date", "-created_at")


# -------------------------
# PROJECTS ADMIN
# -------------------------
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "client_name", "start_date", "deadline", "status", "progress_percentage", "created_at")
    list_filter = ("status", "start_date", "deadline")
    search_fields = ("name", "client_name", "description")
    ordering = ("-created_at",)


# -------------------------
# TASKS ADMIN
# -------------------------
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "assigned_to", "due_date", "priority", "status", "created_at")
    list_filter = ("priority", "status", "due_date")
    search_fields = ("title", "assigned_to", "project__name", "description")
    ordering = ("-created_at",)


# -------------------------
# CLIENTS ADMIN
# -------------------------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("company_name", "contact_person", "email", "phone", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("company_name", "contact_person", "email", "phone", "address")
    ordering = ("-created_at",)


# NOTE: Keeping these "simple" avoids admin crash if field names differ.
admin.site.register(Team)
admin.site.register(Payroll)
admin.site.register(Invoice)
admin.site.register(Payment)
admin.site.register(Ticket)
admin.site.register(TicketComment)
admin.site.register(Event)
admin.site.register(Note)
admin.site.register(TimelinePost)
admin.site.register(TimelineComment)
admin.site.register(PersonalTask)