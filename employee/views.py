from datetime import date, datetime
import calendar

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import EmployeeProfile, EmployeeTodo
from hr.models import LeaveRequest as Leave, Announcement, LeaveCategory, Attendance, Event
from core.models import Task


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
    leaves = Leave.objects.filter(user=request.user)
    today = timezone.now().date()
    upcoming_todos = []
    if request.user.groups.filter(name="EMPLOYEE").exists() and not getattr(request.user, "client_profile", None):
        upcoming_todos = list(
            EmployeeTodo.objects.filter(employee=request.user, status="PENDING")
            .filter(Q(due_date__gte=today) | Q(due_date__isnull=True))
            .order_by("due_date")[:5]
        )
    context = {
        "pending_leaves": leaves.filter(status="Pending").count(),
        "upcoming_todos": upcoming_todos,
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
        start_str = request.POST.get("start_date")
        end_str = request.POST.get("end_date")
        reason = request.POST.get("reason")

        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

        # Get or create a default category to avoid FK errors
        default_category, _ = LeaveCategory.objects.get_or_create(
            name="General",
            defaults={"description": "General Leave"}
        )

        Leave.objects.create(
            user=request.user,
            category=default_category,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        messages.success(request, "Leave request submitted.")
        return redirect("employee:employee_leaves")

    leaves = Leave.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "employee/leaves.html", {"leaves": leaves})


@login_required
def employee_tasks(request):
    tasks = Task.objects.filter(assigned_to=request.user)
    return render(request, "employee/tasks.html", {"tasks": tasks})


@login_required
def employee_announcements(request):
    announcements = Announcement.objects.all().order_by("-created_at")
    return render(request, "employee/announcements.html", {"announcements": announcements})


@login_required
def clock_in(request):
    today = timezone.now().date()

    existing = Attendance.objects.filter(user=request.user, date=today).first()

    if existing:
        messages.error(request, "Today's attendance already marked.")
    else:
        Attendance.objects.create(
            user=request.user,
            date=today,
            check_in=timezone.now().time()
        )
        messages.success(request, "Clock In marked successfully.")

    return redirect("employee:employee_dashboard")


@login_required
def clock_out(request):
    today = timezone.now().date()

    attendance = Attendance.objects.filter(user=request.user, date=today).first()

    if not attendance:
        messages.error(request, "You must Clock In first.")
    elif attendance.check_out:
        messages.error(request, "You have already Clocked Out today.")
    else:
        attendance.check_out = timezone.now().time()
        attendance.save()
        messages.success(request, "Clock Out saved successfully.")

    return redirect("employee:employee_dashboard")


@login_required
def attendance_history(request):
    attendances = Attendance.objects.filter(user=request.user).order_by("-date")
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
        
    prev_month = month - 1 if month > 1 else 12
    prev_year  = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year  = year if month < 12 else year + 1

    context = {
        "calendar": cal,
        "month": month,
        "year": year,
        "month_name": calendar.month_name[month],
        "event_dict": event_dict,
        "months": range(1, 13),
        "years": range(today.year - 5, today.year + 6),
        "prev_month": prev_month,
        "prev_year":  prev_year,
        "next_month": next_month,
        "next_year":  next_year,
    }
    return render(request, "employee/events.html", context)


# ==========================================
# Chat System Views
# ==========================================
from hr.models import Conversation, Message
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q

@login_required
def chat_dashboard(request):
    user = request.user
    conversations = user.conversations.all().order_by('-created_at')
    
    User = get_user_model()
    # Employee can chat with HR Admins, Active Employees, And Clients
    available_users = User.objects.filter(is_active=True).exclude(id=user.id).filter(
        Q(profile__role='HR') | 
        Q(profile__role='EMPLOYEE', profile__status='ACTIVE') |
        Q(client_profile__isnull=False, client_profile__is_active=True)
    ).distinct()

    context = {
        'conversations': conversations,
        'active_conversation': None,
        'messages': [],
        'available_users': available_users
    }
    return render(request, "employee/chat.html", context)

@login_required
def chat_room(request, pk):
    user = request.user
    conversation = get_object_or_404(user.conversations, pk=pk)
    
    # Mark messages as read
    Message.objects.filter(conversation=conversation).exclude(sender=user).update(is_read=True)
    
    conversations = user.conversations.all().order_by('-created_at')
    messages = conversation.messages.all()
    
    User = get_user_model()
    available_users = User.objects.filter(is_active=True).exclude(id=user.id).filter(
        Q(profile__role='HR') | 
        Q(profile__role='EMPLOYEE', profile__status='ACTIVE') |
        Q(client_profile__isnull=False, client_profile__is_active=True)
    ).distinct()
    
    context = {
        'conversations': conversations,
        'active_conversation': conversation,
        'messages': messages,
        'available_users': available_users
    }
    return render(request, "employee/chat.html", context)

@login_required
def chat_start(request, user_id):
    User = get_user_model()
    other_user = get_object_or_404(User, id=user_id)
    
    user = request.user
    is_employee = hasattr(user, 'profile') and user.profile.role == 'EMPLOYEE'
    
    target_is_hr = hasattr(other_user, 'profile') and other_user.profile.role == 'HR'
    if getattr(other_user, 'is_superuser', False) and not target_is_hr and not hasattr(other_user, 'profile'): 
        target_is_hr = True
        
    target_is_emp = hasattr(other_user, 'profile') and other_user.profile.role == 'EMPLOYEE'
    target_is_client = hasattr(other_user, 'client_profile')
    
    if not (is_employee and (target_is_hr or target_is_emp or target_is_client)):
        messages.error(request, "You do not have permission to chat with this user.")
        return redirect('employee:chat_dashboard')

    conv = Conversation.objects.filter(is_group=False, participants=request.user).filter(participants=other_user).first()
    
    if not conv:
        conv = Conversation.objects.create(is_group=False)
        conv.participants.add(request.user, other_user)
        
    return redirect('employee:chat_room', pk=conv.id)

@login_required
def chat_delete(request, pk):
    conversation = get_object_or_404(request.user.conversations, pk=pk)
    conversation.delete()
    return redirect('employee:chat_dashboard')


# ==========================================
# Personal To-Do (Employee only)
# ==========================================

def _employee_todo_access(request):
    """Only Employee role can access. Deny HR and Client."""
    if request.user.groups.filter(name="HR").exists():
        return False
    if getattr(request.user, "client_profile", None) is not None:
        return False
    return request.user.groups.filter(name="EMPLOYEE").exists()


@login_required
def employee_todo_list_view(request):
    if not _employee_todo_access(request):
        return HttpResponseForbidden("Only employees can access Personal To-Do.")
    today = timezone.now().date()
    todos_qs = EmployeeTodo.objects.filter(employee=request.user)
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    todos = sorted(
        list(todos_qs),
        key=lambda t: (priority_order.get(t.priority, 1), t.due_date or date.max),
    )
    total = len(todos)
    pending = sum(1 for t in todos if t.status == "PENDING")
    completed = sum(1 for t in todos if t.status == "COMPLETED")
    context = {
        "todos": todos,
        "total_todos": total,
        "pending_count": pending,
        "completed_count": completed,
        "today": today,
    }
    return render(request, "employee/todo_list.html", context)


@login_required
def employee_todo_create_view(request):
    if not _employee_todo_access(request):
        return HttpResponseForbidden("Only employees can access Personal To-Do.")
    if request.method != "POST":
        return redirect("employee:employee_todo_list")
    title = (request.POST.get("title") or "").strip()
    if not title:
        messages.error(request, "Title is required.")
        return redirect("employee:employee_todo_list")
    due_str = request.POST.get("due_date") or None
    due_date = None
    if due_str:
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    EmployeeTodo.objects.create(
        employee=request.user,
        title=title,
        description=(request.POST.get("description") or "").strip(),
        due_date=due_date,
        priority=request.POST.get("priority") or "MEDIUM",
        status="PENDING",
    )
    messages.success(request, "To-Do added.")
    return redirect("employee:employee_todo_list")


@login_required
def employee_todo_update_view(request, pk):
    if not _employee_todo_access(request):
        return HttpResponseForbidden("Only employees can access Personal To-Do.")
    todo = get_object_or_404(EmployeeTodo, pk=pk, employee=request.user)
    if request.method != "POST":
        return redirect("employee:employee_todo_list")
    title = (request.POST.get("title") or "").strip()
    if not title:
        messages.error(request, "Title is required.")
        return redirect("employee:employee_todo_list")
    due_str = request.POST.get("due_date") or None
    due_date = None
    if due_str:
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    todo.title = title
    todo.description = (request.POST.get("description") or "").strip()
    todo.due_date = due_date
    todo.priority = request.POST.get("priority") or "MEDIUM"
    todo.save()
    messages.success(request, "To-Do updated.")
    return redirect("employee:employee_todo_list")


@login_required
def employee_todo_delete_view(request, pk):
    if not _employee_todo_access(request):
        return HttpResponseForbidden("Only employees can access Personal To-Do.")
    todo = get_object_or_404(EmployeeTodo, pk=pk, employee=request.user)
    if request.method == "POST":
        todo.delete()
        messages.success(request, "To-Do deleted.")
    return redirect("employee:employee_todo_list")


@login_required
def employee_todo_toggle_status_view(request, pk):
    if not _employee_todo_access(request):
        return HttpResponseForbidden("Only employees can access Personal To-Do.")
    todo = get_object_or_404(EmployeeTodo, pk=pk, employee=request.user)
    if request.method == "POST":
        todo.status = "COMPLETED" if todo.status == "PENDING" else "PENDING"
        todo.save()
        messages.success(request, f"Marked as {todo.get_status_display().lower()}.")
    return redirect("employee:employee_todo_list")