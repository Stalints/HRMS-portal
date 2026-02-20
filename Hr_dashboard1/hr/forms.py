from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password   

from .models import Attendance
from .models import LeaveCategory, Announcement, Project, Task, Client, Event, Note, TimelinePost, TimelineComment, HelpArticle, HelpCategory, PersonalTask

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
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'status']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'name@company.com'}),
            'role': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }
        labels = {
            'username': 'Username',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'role': 'Role',
            'status': 'Status',
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


class AttendanceForm(forms.ModelForm):
    """Form for manual attendance entry."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(status='ACTIVE').order_by('first_name', 'last_name')
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


class TeamMemberEditForm(forms.ModelForm):
    """Form for editing an existing team member (User)."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'status']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'name@company.com'}),
            'role': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'role': 'Role',
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


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "message", "publish_date"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Enter announcement title"}),
            "message": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 4, "placeholder": "Enter announcement message or description"}),
            "publish_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
        }


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
            "description": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 4, "placeholder": "Enter event description"}),
            "event_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "start_time": forms.TimeInput(attrs={"class": "form-control form-control-sm", "type": "time"}),
            "end_time": forms.TimeInput(attrs={"class": "form-control form-control-sm", "type": "time"}),
            "share_with": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Shared with"}),
            "event_type": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "reminder_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "reminder_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
        }


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "description", "tags", "visibility", "attachment"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter note title", "required": True}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Enter note description", "required": True}),
            "tags": forms.TextInput(attrs={"class": "form-control", "placeholder": "tag1, tag2"}),
            "visibility": forms.Select(attrs={"class": "form-select"}),
            "attachment": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class TimelinePostForm(forms.ModelForm):
    class Meta:
        model = TimelinePost
        fields = ["title", "message", "file_attachment", "link_attachment", "post_type"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter a title for your post"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Share your update, idea, or information...", "required": True}),
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


class HelpArticleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = HelpCategory.objects.order_by("name")
        self.fields["category"].empty_label = "Select a category"
    class Meta:
        model = HelpArticle
        fields = ["title", "category", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter article title", "required": True}),
            "category": forms.Select(attrs={"class": "form-select", "required": True}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 8, "placeholder": "Write the article content here...", "required": True}),
        }


class PersonalTaskForm(forms.ModelForm):
    class Meta:
        model = PersonalTask
        fields = ["description", "due_date"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your task...", "required": True}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }
