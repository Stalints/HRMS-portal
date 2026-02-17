from datetime import date

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .forms import AttendanceForm, TeamMemberAddForm, TeamMemberEditForm, AnnouncementForm, ProjectForm, TaskForm, ClientForm
from .models import Attendance, Status, LeaveRequest, LeaveCategory, Announcement, AnnouncementStatus, Project, Task, TaskStatus, Client, ClientStatus
from .forms import LeaveCategoryForm


User = get_user_model()


# =====================
# DASHBOARD
# =====================

def dashboard(request):
    active_announcements = Announcement.objects.filter(status=AnnouncementStatus.ACTIVE).order_by("-publish_date", "-created_at")[:5]
    return render(request, "hr/dashboard.html", {
        "active_announcements": active_announcements,
        "active_announcements_count": active_announcements.count(),
    })


# =====================
# TEAM MANAGEMENT
# =====================

def team_list(request):
    query = request.GET.get("q", "").strip()

    members = User.objects.all()

    if query:
        members = members.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(username__icontains=query)
        )

    members = members.order_by("-created_at")

    return render(request, "hr/team.html", {
        "members": members,
        "search_query": query,
    })


def team_add(request):
    if request.method == "POST":
        form = TeamMemberAddForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Team member added successfully.")
            return redirect("hr:team_list")
    else:
        form = TeamMemberAddForm()

    return render(request, "hr/team_form.html", {
        "form": form,
        "is_edit": False
    })


def team_edit(request, pk):
    member = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = TeamMemberEditForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, "Team member updated successfully.")
            return redirect("hr:team_list")
    else:
        form = TeamMemberEditForm(instance=member)

    return render(request, "hr/team_form.html", {
        "form": form,
        "member": member,
        "is_edit": True
    })


def team_activate(request, pk):
    member = get_object_or_404(User, pk=pk)
    member.status = Status.ACTIVE
    member.is_active = True
    member.save()

    messages.success(request, f"{member.get_full_name()} activated.")
    return redirect("hr:team_list")


def team_deactivate(request, pk):
    member = get_object_or_404(User, pk=pk)
    member.status = Status.INACTIVE
    member.is_active = False
    member.save()

    messages.success(request, f"{member.get_full_name()} deactivated.")
    return redirect("hr:team_list")


# =====================
# ATTENDANCE
# =====================

def attendance_list(request):
    date_str = request.GET.get("date", "")

    try:
        filter_date = date.fromisoformat(date_str) if date_str else timezone.localdate()
    except ValueError:
        filter_date = timezone.localdate()

    # ---- Save attendance ----
    if request.method == "POST":
        form = AttendanceForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)

            attendance, _ = Attendance.objects.update_or_create(
                user=obj.user,
                date=obj.date,
                defaults={
                    "check_in": obj.check_in,
                    "check_out": obj.check_out,
                    "status": obj.status,
                }
            )

            attendance.save()
            messages.success(request, "Attendance saved.")

            return redirect(
                f"{reverse('hr:attendance_list')}?date={obj.date.isoformat()}"
            )
    else:
        form = AttendanceForm(initial={"date": filter_date})

    # ---- Filters ----
    records = Attendance.objects.filter(date=filter_date).select_related("user")

    status_filter = request.GET.get("status", "")
    if status_filter:
        records = records.filter(status=status_filter.upper())

    employee_query = request.GET.get("employee", "").strip()
    if employee_query:
        records = records.filter(
            Q(user__first_name__icontains=employee_query) |
            Q(user__last_name__icontains=employee_query) |
            Q(user__email__icontains=employee_query)
        )

    context = {
        "records": records,
        "form": form,
        "filter_date": filter_date,
        "date_str": filter_date.isoformat(),
        "total_employees": User.objects.filter(status="ACTIVE").count(),
        "present_today": records.filter(status="PRESENT").count(),
        "absent_today": records.filter(status="ABSENT").count(),
        "late_today": records.filter(status="LATE").count(),
    }

    return render(request, "hr/attendance.html", context)


# =====================
# LEAVE MANAGEMENT
# =====================

def leave_dashboard(request):
    leaves = LeaveRequest.objects.select_related("user", "category")
    categories = LeaveCategory.objects.all()

    context = {
        "leaves": leaves,
        "categories": categories,
        "total_employees": User.objects.count(),
        "total_requests": leaves.count(),
        "approved_count": leaves.filter(status="Approved").count(),
        "pending_count": leaves.filter(status="Pending").count(),
        "rejected_count": leaves.filter(status="Rejected").count(),
        "cat_form": LeaveCategoryForm(),
    }

    return render(request, "hr/leave.html", context)



def approve_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = "Approved"

    if request.user.is_authenticated:
        leave.approved_by = request.user

    leave.save()
    messages.success(request, "Leave approved.")

    return redirect("hr:leave_dashboard")


# =====================
# ANNOUNCEMENTS
# =====================

def announcement_list(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            if request.user.is_authenticated:
                ann.created_by = request.user
            ann.save()
            messages.success(request, "Announcement created.")
            return redirect("hr:announcement_list")
    else:
        form = AnnouncementForm()

    announcements = Announcement.objects.all().order_by("-publish_date", "-created_at")
    return render(request, "hr/announcements.html", {
        "form": form,
        "announcements": announcements,
    })


def announcement_edit(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=ann)
        status_value = request.POST.get("status")
        if form.is_valid():
            obj = form.save(commit=False)
            if status_value in dict(AnnouncementStatus.choices):
                obj.status = status_value
            obj.save()
            messages.success(request, "Announcement updated.")
            return redirect("hr:announcement_list")
    else:
        form = AnnouncementForm(instance=ann)

    return render(request, "hr/announcement_form.html", {
        "form": form,
        "announcement": ann,
        "status_choices": AnnouncementStatus.choices
    })


def announcement_delete(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        ann.delete()
        messages.success(request, "Announcement deleted.")
        return redirect("hr:announcement_list")
    return render(request, "hr/announcement_delete_confirm.html", {"announcement": ann})


# =====================
# PROJECTS
# =====================

def project_list(request):
    projects = Project.objects.all()
    return render(request, "hr/projects.html", {"projects": projects})


def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Project created successfully.")
            return redirect("hr:project_list")
    else:
        form = ProjectForm()
    return render(request, "hr/project_form.html", {"form": form, "is_edit": False})


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, "hr/project_detail.html", {"project": project})


def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated successfully.")
            return redirect("hr:project_detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, "hr/project_form.html", {"form": form, "is_edit": True, "project": project})


def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        project.delete()
        messages.success(request, "Project deleted.")
        return redirect("hr:project_list")
    return render(request, "hr/project_delete_confirm.html", {"project": project})


# =====================
# TASKS
# =====================

def task_list(request):
    status_filter = request.GET.get("status")
    tasks = Task.objects.select_related("project").all()
    if status_filter in dict(TaskStatus.choices).keys():
        tasks = tasks.filter(status=status_filter)
    form = TaskForm()
    return render(request, "hr/tasks.html", {"tasks": tasks, "form": form, "status_filter": status_filter})


def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Task created.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    return redirect("hr:task_list")


def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    return redirect("hr:task_list")


def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted.")
    return redirect("hr:task_list")


def client_list(request):
    clients = Client.objects.all()
    form = ClientForm()
    return render(request, "hr/clients.html", {"clients": clients, "form": form})


def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Client added.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    return redirect("hr:client_list")


def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Client updated.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    return redirect("hr:client_list")


def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        client.delete()
        messages.success(request, "Client deleted.")
    return redirect("hr:client_list")


def reject_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = "Rejected"

    if request.user.is_authenticated:
        leave.approved_by = request.user

    leave.save()
    messages.success(request, "Leave rejected.")

    return redirect("hr:leave_dashboard")


def add_leave_category_ajax(request):
    # Deprecated AJAX handler retained for compatibility if referenced elsewhere.
    # Prefer add_leave_category view for non-API form handling.
    return redirect("hr:add_leave_category")


def add_leave_category(request):
    if request.method == "POST":
        form = LeaveCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Leave category added.")
            return redirect("hr:leave_dashboard")
    else:
        form = LeaveCategoryForm()

    return render(request, "hr/leave_category_form.html", {"form": form})
