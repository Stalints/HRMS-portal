from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin.sites import AlreadyRegistered, NotRegistered

from .models import (
    # User profile & roles
    UserProfile,

    # Core
    Team,
    Attendance,
    LeaveCategory,
    LeaveRequest,
    Announcement,
    Event,
    Notification,
    AdminProfile,

    # Payroll
    Payroll,

    # Notes / Timeline / Help / Personal
    Note,
    TimelinePost,
    TimelineLike,
    TimelineComment,
    HelpCategory,
    HelpArticle,
    PersonalTask,
)

User = get_user_model()


# ---------------------------------------
# User admin (keep default Django fields)
# + show profile role/status in list view
# ---------------------------------------
try:
    admin.site.unregister(User)
except (NotRegistered, AlreadyRegistered):
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
        "profile_role",
        "profile_status",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)
    date_hierarchy = "date_joined"

    @admin.display(description="Role")
    def profile_role(self, obj):
        return getattr(getattr(obj, "profile", None), "role", "")

    @admin.display(description="Status")
    def profile_status(self, obj):
        return getattr(getattr(obj, "profile", None), "status", "")


# -----------------------------
# UserProfile admin
# -----------------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "status", "created_at")
    list_filter = ("role", "status")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


# -----------------------------
# Team
# -----------------------------
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "team_lead", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "team_lead__username", "team_lead__email")
    ordering = ("name",)
    date_hierarchy = "created_at"


# -----------------------------
# Attendance
# -----------------------------
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "check_in", "check_out", "total_hours", "status")
    list_filter = ("date", "status")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    date_hierarchy = "date"
    ordering = ("-date", "user")


# -----------------------------
# Leave
# -----------------------------
@admin.register(LeaveCategory)
class LeaveCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "days_per_year")
    search_fields = ("name",)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "start_date", "end_date", "total_days", "status", "created_at", "approved_by")
    list_filter = ("status", "category")
    search_fields = ("user__username", "user__email", "category__name")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


# -----------------------------
# Announcements
# -----------------------------
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "publish_date", "status", "created_by", "created_at")
    list_filter = ("status", "publish_date")
    search_fields = ("title", "message", "created_by__username", "created_by__email")
    date_hierarchy = "created_at"
    ordering = ("-publish_date", "-created_at")


# -----------------------------
# Events
# -----------------------------
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "event_date", "start_time", "end_time", "event_type", "share_with", "created_by", "created_at")
    list_filter = ("event_type", "event_date", "reminder_enabled", "reminder_sent")
    search_fields = ("title", "description", "share_with", "created_by__username", "created_by__email")
    date_hierarchy = "event_date"
    ordering = ("-event_date", "start_time")


# -----------------------------
# Notifications
# -----------------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("title", "message")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


# -----------------------------
# AdminProfile (your custom settings model)
# -----------------------------
@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "role", "is_active", "member_since")
    list_filter = ("role", "is_active")
    search_fields = ("full_name", "email")


# -----------------------------
# Payroll
# -----------------------------
@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ("employee_name", "month", "gross_salary", "net_salary", "status", "created_at")
    list_filter = ("status", "month")
    search_fields = ("employee_name", "month")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


# -----------------------------
# Notes
# -----------------------------
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "visibility", "created_by", "created_at", "updated_at")
    list_filter = ("visibility",)
    search_fields = ("title", "description", "tags", "created_by__username", "created_by__email")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


# -----------------------------
# Timeline
# -----------------------------
@admin.register(TimelinePost)
class TimelinePostAdmin(admin.ModelAdmin):
    list_display = ("title", "post_type", "created_by", "created_at", "view_count")
    list_filter = ("post_type",)
    search_fields = ("title", "message", "created_by__username", "created_by__email")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(TimelineLike)
class TimelineLikeAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    search_fields = ("post__title", "user__username", "user__email")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(TimelineComment)
class TimelineCommentAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    search_fields = ("post__title", "comment_text", "user__username", "user__email")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


# -----------------------------
# Help Articles
# -----------------------------
@admin.register(HelpCategory)
class HelpCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    ordering = ("name",)


@admin.register(HelpArticle)
class HelpArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_active", "created_by", "created_at", "updated_at")
    list_filter = ("is_active", "category")
    search_fields = ("title", "content", "created_by__username", "created_by__email")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


# -----------------------------
# Personal Tasks
# -----------------------------
@admin.register(PersonalTask)
class PersonalTaskAdmin(admin.ModelAdmin):
    list_display = ("user", "description", "due_date", "is_completed", "created_at")
    list_filter = ("is_completed", "due_date")
    search_fields = ("user__username", "user__email", "description")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)