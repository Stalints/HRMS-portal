from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import EmployeeProfile, Leave, Task, Attendance, Announcement
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import messages


def employee_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('employee_dashboard')
        else:
            return render(request, 'employee/login.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'employee/login.html')

@login_required
def employee_dashboard(request):
    from employee.models import Leave

    leaves = Leave.objects.filter(employee=request.user)

    context = {
        'attendance_count': 18,       # temporary
        'task_count': 6,              # temporary
        'announcement_count': 3,      # temporary
        'pending_leaves': leaves.filter(status='Pending').count(),
    }

    return render(request, 'employee/dashboard.html', context)


@login_required
def employee_profile(request):
    try:
        profile = EmployeeProfile.objects.get(user=request.user)
    except EmployeeProfile.DoesNotExist:
        profile = None

    return render(request, 'employee/profile.html', {'profile': profile})
@login_required
def employee_leaves(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')

        Leave.objects.create(
            employee=request.user,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        return redirect('employee_leaves')

    leaves = Leave.objects.filter(employee=request.user).order_by('-applied_on')
    return render(request, 'employee/leaves.html', {'leaves': leaves})

@login_required
def employee_tasks(request):
    tasks = Task.objects.filter(employee=request.user)
    return render(request, 'employee/tasks.html', {'tasks': tasks})


@login_required
def employee_attendance(request):
    attendance = Attendance.objects.filter(employee=request.user)
    return render(request, 'employee/attendance.html', {'attendance': attendance})


@login_required
def employee_announcements(request):
    announcements = Announcement.objects.all().order_by('-created_at')
    return render(request, 'employee/announcements.html', {'announcements': announcements})




def clock_in(request):
    today = timezone.now().date()

    existing = Attendance.objects.filter(
        employee=request.user,
        date=today
    ).first()

    if existing:
        messages.error(request, "Today's attendance already marked.")
    else:
        Attendance.objects.create(
            employee=request.user,
            date=today,
            clock_in=timezone.now()
        )
        messages.success(request, "Clock In marked successfully.")

    return redirect('employee_dashboard')


def clock_out(request):
    today = timezone.now().date()

    attendance = Attendance.objects.filter(
        employee=request.user,
        date=today
    ).first()

    if not attendance:
        messages.error(request, "You must Clock In first.")
    elif attendance.clock_out:
        messages.error(request, "You have already Clocked Out today.")
    else:
        attendance.clock_out = timezone.now()
        attendance.save()
        messages.success(request, "Clock Out saved successfully.")

    return redirect('employee_dashboard')

from django.utils import timezone
from .models import Attendance

def attendance_history(request):
    attendances = Attendance.objects.filter(
        employee=request.user
    ).order_by('-date')

    return render(request, 'employee/attendance.html', {
        'attendances': attendances
    })
