from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import Attendance
from .models import (
    LeaveCategory,
    Announcement,
    Project,
    Task,
    Client,
    Event,
    Note,
    TimelinePost,
    TimelineComment,
    HelpArticle,
    HelpCategory,
    PersonalTask,
    Team,
    Payroll,
    Invoice,
    Payment,
    Ticket,
    TicketComment,
)

User = get_user_model()


# ─────────────────────────────────────────────────────────────
# Helpers (so this file works with BOTH default auth.User
# and your custom user model that has role/status fields)
# ─────────────────────────────────────────────────────────────
def _user_has_field(field_name: str) -> bool:
    try:
        return User._meta.get_field(field_name) is not None
    except Exception:
        return False


USER_HAS_ROLE = _user_has_field("role")
USER_HAS_STATUS = _user_has_field("status")

# Build safe field lists dynamically at import time
TEAM_MEMBER_ADD_FIELDS = ["username", "first_name", "last_name", "email"]
TEAM_MEMBER_EDIT_FIELDS = ["first_name", "last_name", "email"]

if USER_HAS_ROLE:
    TEAM_MEMBER_ADD_FIELDS.append("role")
    TEAM_MEMBER_EDIT_FIELDS.append("role")

if USER_HAS_STATUS:
    TEAM_MEMBER_ADD_FIELDS.append("status")
    TEAM_MEMBER_EDIT_FIELDS.append("status")


# ─────────────────────────────────────────────────────────────
# Team Member Forms
# ─────────────────────────────────────────────────────────────
class TeamMemberAddForm(forms.ModelForm):
    """Form for adding a new team member (User)."""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-sm"}),
        required=True,
        validators=[validate_password],
        label="Password",
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-sm"}),
        required=True,
        label="Confirm Password",
    )

    class Meta:
        model = User
        fields = TEAM_MEMBER_ADD_FIELDS
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "first_name": forms.TextInput(
                attrs={"class": "form-control form-control-sm", "placeholder": "First name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control form-control-sm", "placeholder": "Last name"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control form-control-sm", "placeholder": "name@company.com"}
            ),
        }
        labels = {
            "username": "Username",
            "first_name": "First Name",
            "last_name": "Last Name",
            "email": "Email",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add role/status widgets only if those fields exist
        if USER_HAS_ROLE and "role" in self.fields:
            self.fields["role"].widget = forms.Select(attrs={"class": "form-select form-select-sm"})
            self.fields["role"].label = "Role"

        if USER_HAS_STATUS and "status" in self.fields:
            self.fields["status"].widget = forms.Select(attrs={"class": "form-select form-select-sm"})
            self.fields["status"].label = "Status"

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        password_confirm = cleaned.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class TeamMemberEditForm(forms.ModelForm):
    """Form for editing an existing team member (User)."""

    class Meta:
        model = User
        fields = TEAM_MEMBER_EDIT_FIELDS
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control form-control-sm", "placeholder": "First name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control form-control-sm", "placeholder": "Last name"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control form-control-sm", "placeholder": "name@company.com"}
            ),
        }
        labels = {
            "first_name": "First Name",
            "last_name": "Last Name",
            "email": "Email",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if USER_HAS_ROLE and "role" in self.fields:
            self.fields["role"].widget = forms.Select(attrs={"class": "form-select form-select-sm"})
            self.fields["role"].label = "Role"

        if USER_HAS_STATUS and "status" in self.fields:
            self.fields["status"].widget = forms.Select(attrs={"class": "form-select form-select-sm"})
            self.fields["status"].label = "Status"


# ─────────────────────────────────────────────────────────────
# Attendance
# ─────────────────────────────────────────────────────────────
class AttendanceForm(forms.ModelForm):
    """Form for manual attendance entry."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If your User has status="ACTIVE" use it, else default auth user uses is_active=True
        qs = User.objects.all()
        if USER_HAS_STATUS:
            qs = qs.filter(status="ACTIVE")
        else:
            qs = qs.filter(is_active=True)

        self.fields["user"].queryset = qs.order_by("first_name", "last_name", "username")

        self.fields["check_in"].required = False
        self.fields["check_out"].required = False

    class Meta:
        model = Attendance
        fields = ["user", "date", "check_in", "check_out", "status"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "check_in": forms.TimeInput(attrs={"class": "form-control form-control-sm", "type": "time"}),
            "check_out": forms.TimeInput(attrs={"class": "form-control form-control-sm", "type": "time"}),
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
        }
        labels = {
            "user": "Employee",
            "date": "Date",
            "check_in": "Check-in",
            "check_out": "Check-out",
            "status": "Status",
        }


# ─────────────────────────────────────────────────────────────
# Team
# ─────────────────────────────────────────────────────────────
class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "description", "team_lead", "members", "status"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter team name"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Team description (optional)"}
            ),
            "team_lead": forms.Select(attrs={"class": "form-select"}),
            "members": forms.SelectMultiple(attrs={"class": "form-select", "size": 8}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "name": "Team Name",
            "description": "Description",
            "team_lead": "Team Lead",
            "members": "Members",
            "status": "Status",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        employees = User.objects.order_by("first_name", "last_name", "username")
        self.fields["team_lead"].queryset = employees
        self.fields["team_lead"].required = False
        self.fields["members"].queryset = employees


# ─────────────────────────────────────────────────────────────
# Leave + Announcement
# ─────────────────────────────────────────────────────────────
class LeaveCategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "days_per_year" in self.fields:
            self.fields["days_per_year"].required = False

    class Meta:
        model = LeaveCategory
        fields = ["name", "description", "days_per_year"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Category name"}),
            "description": forms.Textarea(
                attrs={"class": "form-control form-control-sm", "rows": 3, "placeholder": "Description (optional)"}
            ),
            "days_per_year": forms.NumberInput(
                attrs={"class": "form-control form-control-sm", "placeholder": "Days per year"}
            ),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "message", "publish_date"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control form-control-sm", "placeholder": "Enter announcement title"}
            ),
            "message": forms.Textarea(
                attrs={"class": "form-control form-control-sm", "rows": 4, "placeholder": "Enter announcement message"}
            ),
            "publish_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
        }


# ─────────────────────────────────────────────────────────────
# Projects + Tasks + Clients
# ─────────────────────────────────────────────────────────────
class ProjectForm(forms.ModelForm):
    client_name = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        client_choices = [("", "Select Client")]
        for client in Client.objects.order_by("company_name"):
            client_choices.append((client.company_name, client.company_name))

        current_value = self.initial.get("client_name") or getattr(self.instance, "client_name", "")
        if current_value and current_value not in dict(client_choices):
            client_choices.append((current_value, current_value))

        self.fields["client_name"].choices = client_choices

    class Meta:
        model = Project
        fields = [
            "name",
            "client_name",
            "start_date",
            "deadline",
            "status",
            "progress_percentage",
            "description",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Project name"}),
            "start_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "deadline": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "progress_percentage": forms.NumberInput(
                attrs={"class": "form-control form-control-sm", "min": 0, "max": 100}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control form-control-sm", "rows": 4, "placeholder": "Describe the project"}
            ),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "project", "assigned_to", "due_date", "priority", "status", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Task title"}),
            "project": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "assigned_to": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Assignee name"}),
            "due_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "priority": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "description": forms.Textarea(
                attrs={"class": "form-control form-control-sm", "rows": 3, "placeholder": "Task details"}
            ),
        }


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["company_name", "contact_person", "email", "phone", "address", "status"]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Company name"}),
            "contact_person": forms.TextInput(
                attrs={"class": "form-control form-control-sm", "placeholder": "Contact person"}
            ),
            "email": forms.EmailInput(attrs={"class": "form-control form-control-sm", "placeholder": "email@example.com"}),
            "phone": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Phone number"}),
            "address": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 3, "placeholder": "Address"}),
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
        }


# ─────────────────────────────────────────────────────────────
# Payroll
# ─────────────────────────────────────────────────────────────
class PayrollForm(forms.ModelForm):
    employee_name = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        employees = User.objects.filter(is_superuser=False).order_by("first_name", "last_name", "username")
        choices = [("", "Select Employee")]
        for employee in employees:
            value = employee.get_full_name().strip() or employee.username
            choices.append((value, value))

        current_value = self.initial.get("employee_name") or getattr(self.instance, "employee_name", "")
        if current_value and current_value not in dict(choices):
            choices.append((current_value, current_value))

        self.fields["employee_name"].choices = choices

    class Meta:
        model = Payroll
        fields = ["employee_name", "month", "basic_salary", "allowances", "deductions", "status"]
        widgets = {
            "month": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "e.g., February 2026"}),
            "basic_salary": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01", "min": "0"}),
            "allowances": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01", "min": "0"}),
            "deductions": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01", "min": "0"}),
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
        }


# ─────────────────────────────────────────────────────────────
# Events
# ─────────────────────────────────────────────────────────────
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "event_date",
            "start_time",
            "end_time",
            "share_with",
            "event_type",
            "reminder_enabled",
            "reminder_date",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Enter event title"}),
            "description": forms.Textarea(
                attrs={"class": "form-control form-control-sm", "rows": 4, "placeholder": "Enter event description"}
            ),
            "event_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "start_time": forms.TimeInput(attrs={"class": "form-control form-control-sm", "type": "time"}),
            "end_time": forms.TimeInput(attrs={"class": "form-control form-control-sm", "type": "time"}),
            "share_with": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Shared with"}),
            "event_type": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "reminder_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "reminder_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
        }


# ─────────────────────────────────────────────────────────────
# Invoice + Payment
# ─────────────────────────────────────────────────────────────
class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["client", "project", "amount", "tax_percentage", "due_date", "status"]
        widgets = {
            "client": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "project": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "amount": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01", "min": "0"}),
            "tax_percentage": forms.NumberInput(attrs={"class": "form-control form-control-sm", "step": "0.01", "min": "0"}),
            "due_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount_paid", "payment_date", "payment_method", "reference_number"]
        widgets = {
            "amount_paid": forms.NumberInput(
                attrs={"class": "form-control form-control-sm", "step": "0.01", "min": "0.01"}
            ),
            "payment_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "payment_method": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "reference_number": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Optional reference"}),
        }


# ─────────────────────────────────────────────────────────────
# Tickets
# ─────────────────────────────────────────────────────────────
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["client", "project", "subject", "description", "priority", "assigned_to", "status"]
        widgets = {
            "client": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "project": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "subject": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Ticket subject"}),
            "description": forms.Textarea(
                attrs={"class": "form-control form-control-sm", "rows": 4, "placeholder": "Describe the issue"}
            ),
            "priority": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "assigned_to": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].required = False
        self.fields["assigned_to"].required = False
        self.fields["assigned_to"].queryset = User.objects.filter(is_superuser=False).order_by(
            "first_name", "last_name", "username"
        )
        self.fields["assigned_to"].empty_label = "Unassigned"


class TicketManagementForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["priority", "status", "assigned_to"]
        widgets = {
            "priority": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "assigned_to": forms.Select(attrs={"class": "form-select form-select-sm"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].required = False
        self.fields["assigned_to"].queryset = User.objects.filter(is_superuser=False).order_by(
            "first_name", "last_name", "username"
        )
        self.fields["assigned_to"].empty_label = "Unassigned"


class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ["comment_text"]
        widgets = {
            "comment_text": forms.Textarea(
                attrs={"class": "form-control form-control-sm", "rows": 3, "placeholder": "Add an update/comment"}
            ),
        }


# ─────────────────────────────────────────────────────────────
# Notes
# ─────────────────────────────────────────────────────────────
class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "description", "tags", "visibility", "attachment"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter note title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Enter note description"}),
            "tags": forms.TextInput(attrs={"class": "form-control", "placeholder": "tag1, tag2"}),
            "visibility": forms.Select(attrs={"class": "form-select"}),
            "attachment": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


# ─────────────────────────────────────────────────────────────
# Timeline
# ─────────────────────────────────────────────────────────────
class TimelinePostForm(forms.ModelForm):
    class Meta:
        model = TimelinePost
        fields = ["title", "message", "file_attachment", "link_attachment", "post_type"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter a title for your post"}),
            "message": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Share your update, idea, or information..."}
            ),
            "file_attachment": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "link_attachment": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://example.com"}),
            "post_type": forms.Select(attrs={"class": "form-select"}),
        }


class TimelineCommentForm(forms.ModelForm):
    class Meta:
        model = TimelineComment
        fields = ["comment_text"]
        widgets = {
            "comment_text": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Write a comment..."}),
        }


# ─────────────────────────────────────────────────────────────
# Help Center
# ─────────────────────────────────────────────────────────────
class HelpArticleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = HelpCategory.objects.order_by("name")
        self.fields["category"].empty_label = "Select a category"

    class Meta:
        model = HelpArticle
        fields = ["title", "category", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter article title"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 8, "placeholder": "Write the article content here..."}),
        }


# ─────────────────────────────────────────────────────────────
# Personal Tasks
# ─────────────────────────────────────────────────────────────
class PersonalTaskForm(forms.ModelForm):
    class Meta:
        model = PersonalTask
        fields = ["description", "due_date"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your task..."}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }