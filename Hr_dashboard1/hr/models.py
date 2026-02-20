from django.conf import settings
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models


# -------------------------
# USER + ROLES
# -------------------------

class Role(models.TextChoices):
    HR = 'HR', 'HR'
    MANAGER = 'MANAGER', 'Manager'
    EMPLOYEE = 'EMPLOYEE', 'Employee'


class Status(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)


# -------------------------
# ATTENDANCE
# -------------------------

class AttendanceStatus(models.TextChoices):
    PRESENT = 'PRESENT', 'Present'
    ABSENT = 'ABSENT', 'Absent'
    LATE = 'LATE', 'Late'


class Attendance(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendances',
    )
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0, editable=False)
    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
    )

    class Meta:
        ordering = ['-date', 'user']
        unique_together = [['user', 'date']]
        verbose_name_plural = 'Attendance records'

    def save(self, *args, **kwargs):
        if self.check_in and self.check_out:
            from datetime import datetime
            from decimal import Decimal
            delta = datetime.combine(self.date, self.check_out) - datetime.combine(self.date, self.check_in)
            self.total_hours = Decimal(str(delta.total_seconds() / 3600)).quantize(Decimal('0.01'))
        else:
            self.total_hours = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.get_full_name()} - {self.date} ({self.get_status_display()})'


class LeaveCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    days_per_year = models.IntegerField(default=0)   # added for template usage

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(LeaveCategory, on_delete=models.CASCADE)

    # renamed to match your template
    start_date = models.DateField()
    end_date = models.DateField()

    total_days = models.IntegerField(editable=False)

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_leaves"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.start_date and self.end_date:
            self.total_days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.category.name}"

    class Meta:
        ordering = ["-created_at"]


# -------------------------
# ANNOUNCEMENTS
# -------------------------

class AnnouncementStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    EXPIRED = 'EXPIRED', 'Expired'


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    publish_date = models.DateField()
    status = models.CharField(max_length=20, choices=AnnouncementStatus.choices, default=AnnouncementStatus.ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-publish_date', '-created_at']

    def __str__(self):
        return self.title


# -------------------------
# EVENTS
# -------------------------

class EventType(models.TextChoices):
    MEETING = "MEETING", "Meeting"
    HOLIDAY = "HOLIDAY", "Holiday"
    BIRTHDAY = "BIRTHDAY", "Birthday"
    OTHER = "OTHER", "Other"


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    share_with = models.CharField(max_length=255)
    event_type = models.CharField(max_length=20, choices=EventType.choices, default=EventType.MEETING)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reminder_sent = models.BooleanField(default=False)
    reminder_enabled = models.BooleanField(default=True)
    reminder_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["event_date", "start_time"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.reminder_enabled and not self.reminder_date and self.event_date:
            self.reminder_date = self.event_date - timedelta(days=1)
        super().save(*args, **kwargs)


# -------------------------
# PROJECTS
# -------------------------

class ProjectStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    IN_PROGRESS = "In Progress", "In Progress"
    COMPLETED = "Completed", "Completed"


class Project(models.Model):
    name = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255)
    start_date = models.DateField()
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.PENDING)
    progress_percentage = models.IntegerField(default=0)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


# -------------------------
# TASKS
# -------------------------

class TaskPriority(models.TextChoices):
    LOW = "Low", "Low"
    MEDIUM = "Medium", "Medium"
    HIGH = "High", "High"


class TaskStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    IN_PROGRESS = "In Progress", "In Progress"
    COMPLETED = "Completed", "Completed"


class Task(models.Model):
    title = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    assigned_to = models.CharField(max_length=255)
    due_date = models.DateField()
    priority = models.CharField(max_length=10, choices=TaskPriority.choices, default=TaskPriority.MEDIUM)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ClientStatus(models.TextChoices):
    ACTIVE = "Active", "Active"
    INACTIVE = "Inactive", "Inactive"


class Client(models.Model):
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    address = models.TextField()
    status = models.CharField(max_length=10, choices=ClientStatus.choices, default=ClientStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.company_name


# -------------------------
# NOTES
# -------------------------

class NoteVisibility(models.TextChoices):
    PRIVATE = "PRIVATE", "Private"
    SHARED = "SHARED", "Shared"


class Note(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    tags = models.CharField(max_length=255, blank=True)
    visibility = models.CharField(max_length=10, choices=NoteVisibility.choices, default=NoteVisibility.PRIVATE)
    attachment = models.FileField(upload_to="notes/", null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# -------------------------
# TIMELINE
# -------------------------

class TimelinePostType(models.TextChoices):
    UPDATE = "UPDATE", "Update"
    IDEA = "IDEA", "Idea"
    DOCUMENT = "DOCUMENT", "Document"
    INFORMATION = "INFORMATION", "Information"


class TimelinePost(models.Model):
    title = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    file_attachment = models.FileField(upload_to="timeline/", null=True, blank=True)
    link_attachment = models.URLField(blank=True)
    post_type = models.CharField(max_length=20, choices=TimelinePostType.choices, default=TimelinePostType.UPDATE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="timeline_posts")
    created_at = models.DateTimeField(auto_now_add=True)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or self.message[:50]


class TimelineLike(models.Model):
    post = models.ForeignKey(TimelinePost, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="timeline_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("post", "user")]


class TimelineComment(models.Model):
    post = models.ForeignKey(TimelinePost, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="timeline_comments")
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


# -------------------------
# HELP ARTICLES
# -------------------------
from django.utils.text import slugify

class HelpCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class HelpArticle(models.Model):
    title = models.CharField(max_length=255)
    category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE, related_name="articles")
    content = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="help_articles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

# -------------------------
# PERSONAL TO-DO
# -------------------------
class PersonalTask(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="personal_tasks")
    description = models.CharField(max_length=255)
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_completed", "due_date", "-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.description[:50]}"
