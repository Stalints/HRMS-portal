from datetime import date

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .forms import AttendanceForm, TeamMemberAddForm, TeamMemberEditForm
from .models import Attendance, Status, LeaveRequest, LeaveCategory
from .forms import LeaveCategoryForm

from django.contrib.auth.decorators import login_required

User = get_user_model()


# =====================
# DASHBOARD
# =====================

@login_required
def dashboard(request):
    return render(request, "hr/dashboard.html")


# =====================
# TEAM MANAGEMENT
# =====================

@login_required
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

    members = members.order_by("-date_joined")

    return render(request, "hr/team.html", {
        "members": members,
        "search_query": query,
    })


@login_required
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


@login_required
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


@login_required
def team_activate(request, pk):
    member = get_object_or_404(User, pk=pk)

    member.hr_profile.status = Status.ACTIVE
    member.is_active = True
    member.save()
    member.hr_profile.save()

    messages.success(request, f"{member.get_full_name()} activated.")
    return redirect("hr:team_list")


@login_required
def team_deactivate(request, pk):
    member = get_object_or_404(User, pk=pk)

    member.hr_profile.status = Status.INACTIVE
    member.is_active = False
    member.save()
    member.hr_profile.save()

    messages.success(request, f"{member.get_full_name()} deactivated.")
    return redirect("hr:team_list")


# =====================
# ATTENDANCE
# =====================

@login_required
def attendance_list(request):
    date_str = request.GET.get("date", "")

    try:
        filter_date = date.fromisoformat(date_str) if date_str else timezone.localdate()
    except ValueError:
        filter_date = timezone.localdate()

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
        "total_employees": User.objects.filter(hr_profile__status="ACTIVE").count(),
        "present_today": records.filter(status="PRESENT").count(),
        "absent_today": records.filter(status="ABSENT").count(),
        "late_today": records.filter(status="LATE").count(),
    }

    return render(request, "hr/attendance.html", context)


# =====================
# LEAVE MANAGEMENT
# =====================

@login_required
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
    }

    return render(request, "leave.html", context)


@login_required
def approve_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = "Approved"

    leave.approved_by = request.user
    leave.save()

    messages.success(request, "Leave approved.")
    return redirect("hr:leave_dashboard")


@login_required
def reject_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = "Rejected"

    leave.approved_by = request.user
    leave.save()

    messages.success(request, "Leave rejected.")
    return redirect("hr:leave_dashboard")


@login_required
def add_leave_category_ajax(request):
    if request.method == "POST":
        form = LeaveCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            return JsonResponse({
                "success": True,
                "name": cat.name,
                "days": cat.days_per_year
            })
        else:
            return JsonResponse({"success": False, "errors": form.errors})

    return JsonResponse({"success": False})
