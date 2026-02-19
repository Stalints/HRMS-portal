# ✅ keep these imports as you already have
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import Attendance, LeaveCategory, LeaveRequest, Announcement, Project, Task, Client


User = get_user_model()


class TeamMemberAddForm(forms.ModelForm):
    """Form for adding a new team member (User)."""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-sm'}),
        required=True,
        validators=[validate_password],
        label='Password',
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-sm'}),
        required=True,
        label='Confirm Password',
    )

    class Meta:
        model = User
        # ✅ REMOVED role, status (they don't exist on default Django User)
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'name@company.com'}),
        }
        labels = {
            'username': 'Username',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
        }

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords do not match.')
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class TeamMemberEditForm(forms.ModelForm):
    """Form for editing an existing team member (User)."""

    class Meta:
        model = User
        # ✅ REMOVED role, status
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'name@company.com'}),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
        }


class AttendanceForm(forms.ModelForm):
    """Form for manual attendance entry."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ✅ removed status filter (default User doesn't have status)
        self.fields['user'].queryset = User.objects.all().order_by('first_name', 'last_name')
        self.fields['check_in'].required = False
        self.fields['check_out'].required = False

    class Meta:
        model = Attendance
        fields = ['user', 'date', 'check_in', 'check_out', 'status']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'date': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'check_in': forms.TimeInput(attrs={'class': 'form-control form-control-sm', 'type': 'time'}),
            'check_out': forms.TimeInput(attrs={'class': 'form-control form-control-sm', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }
        labels = {
            'user': 'Employee',
            'date': 'Date',
            'check_in': 'Check-in',
            'check_out': 'Check-out',
            'status': 'Status',
        }

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
            "description": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 3, "placeholder": "Description (optional)"}),
            "days_per_year": forms.NumberInput(attrs={"class": "form-control form-control-sm", "placeholder": "Days per year"}),
        }


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["user", "category", "start_date", "end_date", "reason"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "category": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "start_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "reason": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 3}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "message", "publish_date"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Enter announcement title"}),
            "message": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 4, "placeholder": "Enter announcement message or description"}),
            "publish_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
        }

    def save(self, user=None, commit=True):
        obj = super().save(commit=False)
        if user is not None:
            obj.created_by = user
        if commit:
            obj.save()
        return obj



class ProjectForm(forms.ModelForm):
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
            "client_name": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Client name"}),
            "start_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "deadline": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "progress_percentage": forms.NumberInput(attrs={"class": "form-control form-control-sm", "min": 0, "max": 100}),
            "description": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 4, "placeholder": "Describe the project"}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "project",
            "assigned_to",
            "due_date",
            "priority",
            "status",
            "description",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Task title"}),
            "project": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "assigned_to": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Assignee name"}),
            "due_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "priority": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "description": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 3, "placeholder": "Task details"}),
        }


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            "company_name",
            "contact_person",
            "email",
            "phone",
            "address",
            "status",
        ]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Company name"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Contact person"}),
            "email": forms.EmailInput(attrs={"class": "form-control form-control-sm", "placeholder": "email@example.com"}),
            "phone": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Phone number"}),
            "address": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 3, "placeholder": "Address"}),
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
        }
