from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import Attendance, LeaveCategory, HRProfile  # ✅ HRProfile added

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

    # ✅ ADD these fields (since they are NOT in User anymore)
    role = forms.ChoiceField(
        choices=HRProfile._meta.get_field("role").choices,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='Role',
    )
    status = forms.ChoiceField(
        choices=HRProfile._meta.get_field("status").choices,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='Status',
    )

    class Meta:
        model = User
        # ✅ removed role,status from User model fields
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

            # ✅ Save role/status into HRProfile
            HRProfile.objects.update_or_create(
                user=user,
                defaults={
                    "role": self.cleaned_data["role"],
                    "status": self.cleaned_data["status"],
                }
            )

        return user


class AttendanceForm(forms.ModelForm):
    """Form for manual attendance entry."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ CHANGED: User.status doesn't exist -> use hr_profile__status
        self.fields['user'].queryset = User.objects.filter(
            hr_profile__status="ACTIVE"
        ).order_by('first_name', 'last_name')

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

    # ✅ ADD these fields (since they are NOT in User anymore)
    role = forms.ChoiceField(
        choices=HRProfile._meta.get_field("role").choices,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='Role',
    )
    status = forms.ChoiceField(
        choices=HRProfile._meta.get_field("status").choices,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='Status',
    )

    class Meta:
        model = User
        # ✅ removed role,status from User model fields
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Load initial role/status from HRProfile
        if self.instance and hasattr(self.instance, "hr_profile"):
            self.fields["role"].initial = self.instance.hr_profile.role
            self.fields["status"].initial = self.instance.hr_profile.status

    def save(self, commit=True):
        user = super().save(commit=commit)

        # ✅ Save role/status into HRProfile
        HRProfile.objects.update_or_create(
            user=user,
            defaults={
                "role": self.cleaned_data["role"],
                "status": self.cleaned_data["status"],
            }
        )

        return user


class LeaveCategoryForm(forms.ModelForm):
    class Meta:
        model = LeaveCategory
        fields = ["name", "description", "days_per_year"]
