from django.conf import settings
from django.db import models
from decimal import Decimal
from datetime import datetime

# ✅ ADDED (only for signal)
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver


# -------------------------
# USER ROLES & STATUS
# -------------------------

class Role(models.TextChoices):
    HR = 'HR', 'HR'
    CLIENT = 'CLIENT', 'Client'
    EMPLOYEE = 'EMPLOYEE', 'Employee'


class Status(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'


class HRProfile(models.Model):
    """
    Profile model for users to store role and status.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hr_profile'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# ✅ ADDED (only): Auto-create HRProfile for every new user
@receiver(post_save, sender=get_user_model())
def create_hr_profile(sender, instance, created, **kwargs):
    if created:
        HRProfile.objects.create(user=instance)


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
        related_name='attendances'
    )
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), editable=False)
    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT
    )

    class Meta:
        ordering = ['-date', 'user']
        unique_together = [['user', 'date']]
        verbose_name_plural = 'Attendance Records'

    def save(self, *args, **kwargs):
        """Calculate total hours automatically if check-in and check-out exist."""
        if self.check_in and self.check_out:
            delta = datetime.combine(self.date, self.check_out) - datetime.combine(self.date, self.check_in)
            self.total_hours = Decimal(delta.total_seconds() / 3600).quantize(Decimal('0.01'))
        else:
            self.total_hours = Decimal('0.00')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.get_full_name()} - {self.date} ({self.get_status_display()})'


# -------------------------
# LEAVE MANAGEMENT
# -------------------------

class LeaveCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    days_per_year = models.IntegerField(default=0)   # for template usage

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    category = models.ForeignKey(
        LeaveCategory,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
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

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        """Automatically calculate total days for the leave request."""
        if self.start_date and self.end_date:
            self.total_days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.category.name} ({self.status})"
