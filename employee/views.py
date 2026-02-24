from datetime import date
import calendar

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from hr.models import Event
from .models import EmployeeProfile, Leave, Task, Attendance, Announcement


def employee_login(request):
    # If already logged in, go to dashboard
    if request.user.is_authenticated:
        return redirect("employee:employee_dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("employee:employee_dashboard")
        else:
            return render(request, "employee/login.html", {
                "error": "Invalid username or password"
            })

    return render(request, "employee/login.html")


@login_required
def employee_logout(request):
    logout(request)
    return redirect("login")   # accounts login


@login_required
def employee_dashboard(request):
    leaves = Leave.objects.filter(employee=request.user)

    context = {
        "pending_leaves": leaves.filter(status="Pending").count(),
    }
    return render(request, "employee/dashboard.html", context)


@login_required
def employee_profile(request):
    # Ensure profile always exists
    profile, _ = EmployeeProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "emp_id": f"EMP-{request.user.id}",
            "department": "",
            "designation": "",
            "phone": "",
            "date_joined": timezone.now().date(),
        }
    )

    if request.method == "POST":
        # Update text fields (safe fallback to existing values)
        profile.emp_id = request.POST.get("emp_id", profile.emp_id)
        profile.department = request.POST.get("department", profile.department)
        profile.designation = request.POST.get("designation", profile.designation)
        profile.phone = request.POST.get("phone", profile.phone)

        # ✅ Save uploaded image
        if "profile_image" in request.FILES:
            profile.profile_image = request.FILES["profile_image"]

        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("employee:employee_profile")

    return render(request, "employee/profile.html", {"profile": profile})


@login_required
def employee_leaves(request):
    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        reason = request.POST.get("reason")

        Leave.objects.create(
            employee=request.user,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        messages.success(request, "Leave request submitted.")
        return redirect("employee:employee_leaves")

    leaves = Leave.objects.filter(employee=request.user).order_by("-applied_on")
    return render(request, "employee/leaves.html", {"leaves": leaves})


@login_required
def employee_tasks(request):
    tasks = Task.objects.filter(employee=request.user)
    return render(request, "employee/tasks.html", {"tasks": tasks})


@login_required
def employee_announcements(request):
    announcements = Announcement.objects.all().order_by("-created_at")
    return render(request, "employee/announcements.html", {"announcements": announcements})


@login_required
def clock_in(request):
    today = timezone.now().date()

    existing = Attendance.objects.filter(employee=request.user, date=today).first()

    if existing:
        messages.error(request, "Today's attendance already marked.")
    else:
        Attendance.objects.create(
            employee=request.user,
            date=today,
            clock_in=timezone.now()
        )
        messages.success(request, "Clock In marked successfully.")

    return redirect("employee:employee_dashboard")


@login_required
def clock_out(request):
    today = timezone.now().date()

    attendance = Attendance.objects.filter(employee=request.user, date=today).first()

    if not attendance:
        messages.error(request, "You must Clock In first.")
    elif attendance.clock_out:
        messages.error(request, "You have already Clocked Out today.")
    else:
        attendance.clock_out = timezone.now()
        attendance.save()
        messages.success(request, "Clock Out saved successfully.")

    return redirect("employee:employee_dashboard")


@login_required
def attendance_history(request):
    attendances = Attendance.objects.filter(employee=request.user).order_by("-date")
    return render(request, "employee/attendance.html", {"attendances": attendances})




@login_required
def employee_events(request):
    today = date.today()

    month = request.GET.get("month")
    year = request.GET.get("year")

    if month and year:
        month = int(month)
        year = int(year)
    else:
        month = today.month
        year = today.year

    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    cal = calendar.monthcalendar(year, month)

    events = Event.objects.filter(event_date__year=year, event_date__month=month)

    event_dict = {}
    for event in events:
        event_dict.setdefault(event.event_date.day, []).append(event)

    context = {
        "calendar": cal,
        "month": month,
        "year": year,
        "month_name": calendar.month_name[month],
        "event_dict": event_dict,
        "months": range(1, 13),
        "years": range(today.year - 5, today.year + 6),
    }
    return render(request, "employee/events.html", context)