from datetime import date, timedelta
from calendar import monthrange
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import Q, F, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
import re

from .forms import AttendanceForm, TeamMemberAddForm, TeamMemberEditForm, AnnouncementForm, ProjectForm, TaskForm, ClientForm, TeamForm, PayrollForm, InvoiceForm, TicketManagementForm, TicketCommentForm
from .models import Attendance, Status, LeaveRequest, LeaveCategory, Announcement, AnnouncementStatus, Project, Task, TaskStatus, Client, ClientStatus, Team, Payroll, Invoice, Payment, Ticket, TicketComment
from .forms import LeaveCategoryForm
from .forms import EventForm, NoteForm, TimelinePostForm, TimelineCommentForm, HelpArticleForm, PersonalTaskForm
from .models import (
    Event,
    Role,
    Note,
    NoteVisibility,
    TimelinePost,
    TimelineLike,
    TimelineComment,
    HelpArticle,
    HelpCategory,
    PersonalTask,
    Notification,
    NotificationType,
    AdminProfile,
)
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.contrib.auth import logout


User = get_user_model()


def _create_notification(title: str, message: str, notification_type: str) -> None:
    if notification_type not in dict(NotificationType.choices):
        notification_type = NotificationType.ANNOUNCEMENT
    Notification.objects.create(
        title=title[:255],
        message=message,
        type=notification_type,
    )
def _employee_total_count():
    # Real-time total employee records across statuses.
    return User.objects.filter(is_superuser=False).count()


def _payroll_summary(queryset):
    totals = queryset.aggregate(
        total_gross_salary=Sum("gross_salary"),
        total_deductions=Sum("deductions"),
        total_net_salary=Sum("net_salary"),
    )
    return {
        "total_employees": _employee_total_count(),
        "total_gross_salary": totals["total_gross_salary"] or 0,
        "total_deductions": totals["total_deductions"] or 0,
        "total_net_salary": totals["total_net_salary"] or 0,
        "paid_count": queryset.filter(status="PAID").count(),
        "pending_count": queryset.filter(status="PENDING").count(),
    }


def _invoice_summary(queryset):
    total_revenue = queryset.aggregate(total=Sum("total_amount"))["total"] or 0
    paid_total = Payment.objects.filter(invoice__in=queryset).aggregate(total=Sum("amount_paid"))["total"] or 0
    pending_total = total_revenue - paid_total
    return {
        "total_invoices": queryset.count(),
        "total_revenue": total_revenue,
        "paid_total": paid_total,
        "pending_total": pending_total if pending_total > 0 else 0,
        "overdue_count": queryset.filter(due_date__lt=timezone.localdate()).exclude(status="PAID").count(),
    }


def _ticket_summary(queryset):
    return {
        "total_tickets": queryset.count(),
        "open_tickets_count": queryset.filter(status="OPEN").count(),
        "in_progress_tickets_count": queryset.filter(status="IN_PROGRESS").count(),
        "closed_tickets_count": queryset.filter(status="CLOSED").count(),
    }



# =====================
# DASHBOARD
# =====================

def dashboard(request):
    today = timezone.localdate()
    now = timezone.now()

    employees_qs = User.objects.filter(is_superuser=False)
    total_employees = employees_qs.count()

    attendance_today_qs = Attendance.objects.filter(date=today)
    present_today = attendance_today_qs.filter(status="PRESENT").count()
    attendance_percent = round((present_today / total_employees) * 100) if total_employees else 0

    leaves_qs = LeaveRequest.objects.all()
    pending_leave_requests = leaves_qs.filter(status="Pending").count()
    pending_leave_older_24h = leaves_qs.filter(
        status="Pending",
        created_at__lte=now - timedelta(hours=24),
    ).count()

    active_announcements_qs = Announcement.objects.filter(status=AnnouncementStatus.ACTIVE).order_by("-publish_date", "-created_at")
    active_announcements = active_announcements_qs[:5]
    active_announcements_count = active_announcements_qs.count()
    announcements_this_week = active_announcements_qs.filter(publish_date__gte=today - timedelta(days=6)).count()

    tickets_qs = Ticket.objects.select_related("client").order_by("-created_at")
    recent_tickets = tickets_qs[:5]
    open_tickets_count = tickets_qs.filter(status="OPEN").count()
    high_priority_tickets_count = tickets_qs.filter(priority="HIGH").exclude(status__in=["RESOLVED", "CLOSED"]).count()

    payroll_qs = Payroll.objects.all().order_by("-created_at")
    payroll_total_net = payroll_qs.aggregate(total=Sum("net_salary"))["total"] or 0
    this_month_payroll_total = payroll_qs.filter(
        created_at__year=today.year,
        created_at__month=today.month,
    ).aggregate(total=Sum("net_salary"))["total"] or 0
    payroll_paid_count = payroll_qs.filter(status="PAID").count()
    payroll_pending_count = payroll_qs.filter(status="PENDING").count()
    latest_payroll_records = payroll_qs[:5]

    invoices_qs = Invoice.objects.select_related("client", "project").order_by("-created_at")
    invoice_total_revenue = invoices_qs.aggregate(total=Sum("total_amount"))["total"] or 0
    invoice_paid_count = invoices_qs.filter(status="PAID").count()
    invoice_pending_count = invoices_qs.exclude(status="PAID").count()
    recent_invoices = invoices_qs[:5]

    personal_tasks_qs = PersonalTask.objects.all()
    if request.user.is_authenticated:
        personal_tasks_qs = personal_tasks_qs.filter(user=request.user)
    pending_personal_tasks_count = personal_tasks_qs.filter(is_completed=False).count()
    todo_preview_tasks = personal_tasks_qs.filter(is_completed=False).order_by("due_date", "-created_at")[:3]

    recent_activities = Notification.objects.all().order_by("-created_at")[:6]
    recent_notifications = Notification.objects.all().order_by("-created_at")[:4]
    unread_notifications_count = Notification.objects.filter(is_read=False).count()

    upcoming = Event.objects.filter(event_date__gte=today)
    if request.user.is_authenticated and getattr(getattr(request.user, "profile", None), "role", None) == Role.EMPLOYEE:
        upcoming = upcoming.filter(Q(share_with__icontains="Employee") | Q(share_with__icontains="Team"))
    upcoming = upcoming.order_by("event_date", "start_time")[:5]
    return render(request, "hr/dashboard.html", {
        "total_employees": total_employees,
        "present_today": present_today,
        "attendance_percent": attendance_percent,
        "pending_leave_requests": pending_leave_requests,
        "pending_leave_older_24h": pending_leave_older_24h,
        "active_announcements": active_announcements,
        "active_announcements_count": active_announcements_count,
        "announcements_this_week": announcements_this_week,
        "open_tickets_count": open_tickets_count,
        "high_priority_tickets_count": high_priority_tickets_count,
        "recent_tickets": recent_tickets,
        "payroll_total_net": payroll_total_net,
        "this_month_payroll_total": this_month_payroll_total,
        "payroll_paid_count": payroll_paid_count,
        "payroll_pending_count": payroll_pending_count,
        "latest_payroll_records": latest_payroll_records,
        "invoice_total_revenue": invoice_total_revenue,
        "invoice_paid_count": invoice_paid_count,
        "invoice_pending_count": invoice_pending_count,
        "recent_invoices": recent_invoices,
        "upcoming_events": upcoming,
        "pending_personal_tasks_count": pending_personal_tasks_count,
        "todo_preview_tasks": todo_preview_tasks,
        "recent_activities": recent_activities,
        "recent_notifications": recent_notifications,
        "unread_notifications_count": unread_notifications_count,
    })


# =====================
# EMPLOYEE MANAGEMENT
# =====================

def employee_list(request):
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
    add_form = TeamMemberAddForm()

    return render(request, "hr/employee.html", {
        "members": members,
        "search_query": query,
        "add_form": add_form,
    })


def employee_add(request):
    if request.method == "POST":
        form = TeamMemberAddForm(request.POST)
        if form.is_valid():
            member = form.save()
            _create_notification(
                "Team member added",
                f"{member.get_full_name() or member.username} was added to Team Management.",
                NotificationType.SECURITY,
            )
            messages.success(request, "Team member added successfully.")
            return redirect("hr:employee_list")
        messages.error(request, "Could not add employee. Please check the form values and try again.")
        return redirect("hr:employee_list")
    return redirect("hr:employee_list")


def employee_edit(request, pk):
    member = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = TeamMemberEditForm(request.POST, instance=member)
        if form.is_valid():
            member = form.save()
            _create_notification(
                "Team member updated",
                f"{member.get_full_name() or member.username} profile details were updated.",
                NotificationType.SECURITY,
            )
            messages.success(request, "Team member updated successfully.")
            return redirect("hr:employee_list")
        messages.error(request, "Could not update employee. Please check the form values and try again.")
        return redirect("hr:employee_list")
    return redirect("hr:employee_list")


def employee_activate(request, pk):
    member = get_object_or_404(User, pk=pk)
    member.status = Status.ACTIVE
    member.is_active = True
    member.save()
    _create_notification(
        "Team member activated",
        f"{member.get_full_name() or member.username} was activated.",
        NotificationType.SECURITY,
    )

    messages.success(request, f"{member.get_full_name()} activated.")
    return redirect("hr:employee_list")


def employee_deactivate(request, pk):
    member = get_object_or_404(User, pk=pk)
    member.status = Status.INACTIVE
    member.is_active = False
    member.save()
    _create_notification(
        "Team member deactivated",
        f"{member.get_full_name() or member.username} was deactivated.",
        NotificationType.SECURITY,
    )

    messages.success(request, f"{member.get_full_name()} deactivated.")
    return redirect("hr:employee_list")


# =====================
# TEAM MANAGEMENT
# =====================

def team_list(request):
    teams = Team.objects.select_related("team_lead").prefetch_related("members").order_by("name")
    employees = User.objects.order_by("first_name", "last_name", "username")
    return render(
        request,
        "teams/teams.html",
        {
            "teams": teams,
            "team_form": TeamForm(),
            "employees": employees,
        },
    )


def team_create(request):
    if request.method == "POST":
        form = TeamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Team created successfully.")
            return redirect("hr:team_list")
        messages.error(request, "Could not create team. Please check the form values and try again.")
        return redirect("hr:team_list")
    return redirect("hr:team_list")


def team_detail(request, pk):
    team = get_object_or_404(Team.objects.select_related("team_lead").prefetch_related("members"), pk=pk)
    return render(request, "teams/team_detail.html", {"team": team})


def team_update(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == "POST":
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, "Team updated successfully.")
            return redirect("hr:team_list")
        messages.error(request, "Could not update team. Please check the form values and try again.")
        return redirect("hr:team_list")
    return redirect("hr:team_list")


def team_delete(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == "POST":
        team.delete()
        messages.success(request, "Team deleted successfully.")
        return redirect("hr:team_list")
    return redirect("hr:team_detail", pk=team.pk)


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
            _create_notification(
                "Attendance updated",
                f"Attendance for {attendance.user.get_full_name() or attendance.user.username} on {attendance.date} was saved.",
                NotificationType.ATTENDANCE,
            )
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
        "total_employees": _employee_total_count(),
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
    today = timezone.localdate()
    month_start = today.replace(day=1)
    month_end = today.replace(day=monthrange(today.year, today.month)[1])

    monthly_usage_map = defaultdict(int)
    approved_leaves = leaves.filter(status="Approved").select_related("category")
    for leave in approved_leaves:
        overlap_start = max(leave.start_date, month_start)
        overlap_end = min(leave.end_date, month_end)
        if overlap_start <= overlap_end:
            monthly_usage_map[leave.category.name] += (overlap_end - overlap_start).days + 1

    monthly_leave_usage = [
        {"category_name": cat.name, "days_taken": monthly_usage_map.get(cat.name, 0)}
        for cat in categories
    ]
    monthly_leave_usage.sort(key=lambda x: x["days_taken"], reverse=True)
    monthly_total_days_taken = sum(item["days_taken"] for item in monthly_leave_usage)

    context = {
        "leaves": leaves,
        "categories": categories,
        "total_employees": _employee_total_count(),
        "total_requests": leaves.count(),
        "approved_count": leaves.filter(status="Approved").count(),
        "pending_count": leaves.filter(status="Pending").count(),
        "rejected_count": leaves.filter(status="Rejected").count(),
        "current_month_label": today.strftime("%B %Y"),
        "monthly_leave_usage": monthly_leave_usage,
        "monthly_total_days_taken": monthly_total_days_taken,
        "cat_form": LeaveCategoryForm(),
    }

    return render(request, "hr/leave.html", context)



def approve_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = "Approved"

    if request.user.is_authenticated:
        leave.approved_by = request.user

    leave.save()
    _create_notification(
        "Leave approved",
        f"Leave request #{leave.pk} for {leave.user.get_full_name() or leave.user.username} was approved.",
        NotificationType.LEAVE,
    )
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
            _create_notification(
                "Announcement created",
                f"Announcement '{ann.title}' was published.",
                NotificationType.ANNOUNCEMENT,
            )
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
            _create_notification(
                "Announcement updated",
                f"Announcement '{obj.title}' was updated.",
                NotificationType.ANNOUNCEMENT,
            )
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
        ann_title = ann.title
        ann.delete()
        _create_notification(
            "Announcement deleted",
            f"Announcement '{ann_title}' was removed.",
            NotificationType.ANNOUNCEMENT,
        )
        messages.success(request, "Announcement deleted.")
        return redirect("hr:announcement_list")
    return render(request, "hr/announcement_delete_confirm.html", {"announcement": ann})


# =====================
# PROJECTS
# =====================

def project_list(request):
    projects = Project.objects.all()
    return render(request, "hr/projects.html", {"projects": projects, "project_form": ProjectForm()})


def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            _create_notification(
                "Project created",
                f"Project '{project.name}' was created.",
                NotificationType.ANNOUNCEMENT,
            )
            messages.success(request, "Project created successfully.")
            return redirect("hr:project_list")
        messages.error(request, "Could not create project. Please check the form values and try again.")
        return redirect("hr:project_list")
    return redirect("hr:project_list")


def project_detail(request, pk):
    return redirect("hr:project_list")


def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            _create_notification(
                "Project updated",
                f"Project '{project.name}' was updated.",
                NotificationType.ANNOUNCEMENT,
            )
            messages.success(request, "Project updated successfully.")
            return redirect("hr:project_list")
        messages.error(request, "Could not update project. Please check the form values and try again.")
        return redirect("hr:project_list")
    return redirect("hr:project_list")


def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        project_name = project.name
        project.delete()
        _create_notification(
            "Project deleted",
            f"Project '{project_name}' was deleted.",
            NotificationType.ANNOUNCEMENT,
        )
        messages.success(request, "Project deleted.")
        return redirect("hr:project_list")
    return redirect("hr:project_list")


# =====================
# PAYROLL
# =====================

def payroll_list_view(request):
    payroll_records = Payroll.objects.all().order_by("-created_at")
    context = {
        "payroll_records": payroll_records,
        "form": PayrollForm(),
        "editing": False,
        **_payroll_summary(payroll_records),
    }
    return render(request, "hr/payroll.html", context)


def payroll_create_view(request):
    if request.method == "POST":
        form = PayrollForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Payroll record created.")
    return redirect("hr:payroll_list")


def payroll_update_view(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    if request.method == "POST":
        form = PayrollForm(request.POST, instance=payroll)
        if form.is_valid():
            form.save()
            messages.success(request, "Payroll record updated.")
            return redirect("hr:payroll_list")
    else:
        form = PayrollForm(instance=payroll)

    payroll_records = Payroll.objects.all().order_by("-created_at")
    context = {
        "payroll_records": payroll_records,
        "form": form,
        "editing": True,
        "edit_payroll": payroll,
        **_payroll_summary(payroll_records),
    }
    return render(request, "hr/payroll.html", context)


def payroll_delete_view(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    if request.method == "POST":
        payroll.delete()
        messages.success(request, "Payroll record deleted.")
    return redirect("hr:payroll_list")


def payroll_detail_view(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    return render(request, "hr/payroll_detail.html", {"payroll": payroll})


# =====================
# INVOICES
# =====================

def invoice_list_view(request):
    invoices = Invoice.objects.all().order_by("-created_at")
    context = {
        "invoices": invoices,
        "form": InvoiceForm(),
        "editing": False,
        **_invoice_summary(invoices),
    }
    return render(request, "hr/invoice.html", context)


def invoice_create_view(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Invoice created.")
            return redirect("hr:invoice_list")
    return redirect("hr:invoice_list")


def invoice_update_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, "Invoice updated.")
            return redirect("hr:invoice_list")
    else:
        form = InvoiceForm(instance=invoice)

    invoices = Invoice.objects.all().order_by("-created_at")
    context = {
        "invoices": invoices,
        "form": form,
        "editing": True,
        "edit_invoice": invoice,
        **_invoice_summary(invoices),
    }
    return render(request, "hr/invoice.html", context)


def invoice_delete_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        invoice.delete()
        messages.success(request, "Invoice deleted.")
    return redirect("hr:invoice_list")


def invoice_detail_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    payments = invoice.payments.all().order_by("-payment_date", "-created_at")
    paid_total = payments.aggregate(total=Sum("amount_paid"))["total"] or 0
    balance_due = invoice.total_amount - paid_total
    return render(
        request,
        "hr/invoice_detail.html",
        {
            "invoice": invoice,
            "payments": payments,
            "paid_total": paid_total,
            "balance_due": balance_due if balance_due > 0 else 0,
        },
    )


def payment_list_view(request):
    payments = Payment.objects.all().order_by("-created_at")
    total_payments = payments.aggregate(total=Sum("amount_paid"))["total"] or 0
    return render(
        request,
        "hr/payments.html",
        {
            "payments": payments,
            "payment_count": payments.count(),
            "total_payments": total_payments,
        },
    )


# =====================
# TICKETS
# =====================

def ticket_list_view(request):
    tickets = Ticket.objects.all().order_by("-created_at")
    context = {"tickets": tickets, **_ticket_summary(tickets)}
    return render(request, "hr/ticket_list.html", context)


def ticket_detail_view(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    comments = ticket.comments.all().order_by("created_at")
    comment_form = TicketCommentForm()
    return render(
        request,
        "hr/ticket_detail.html",
        {"ticket": ticket, "comments": comments, "comment_form": comment_form},
    )


def ticket_update_view(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == "POST":
        form = TicketManagementForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ticket {ticket.ticket_id} updated.")
            return redirect("hr:ticket_detail", pk=ticket.pk)
        messages.error(request, "Please correct the errors in the form.")
    else:
        form = TicketManagementForm(instance=ticket)
    return render(request, "hr/ticket_edit.html", {"ticket": ticket, "form": form})


def ticket_delete_view(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == "POST":
        ticket.delete()
        messages.success(request, "Ticket deleted.")
    return redirect("hr:ticket_list")


def ticket_comment_create_view(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if request.method == "POST":
        form = TicketCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.save()
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Comment could not be added.")
    return redirect("hr:ticket_detail", pk=ticket.pk)


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
            task = form.save()
            _create_notification(
                "Task created",
                f"Task '{task.title}' was created in project '{task.project.name}'.",
                NotificationType.ANNOUNCEMENT,
            )
            messages.success(request, "Task created.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    return redirect("hr:task_list")


def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            _create_notification(
                "Task updated",
                f"Task '{task.title}' was updated.",
                NotificationType.ANNOUNCEMENT,
            )
            messages.success(request, "Task updated.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    return redirect("hr:task_list")


def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        task_title = task.title
        task.delete()
        _create_notification(
            "Task deleted",
            f"Task '{task_title}' was deleted.",
            NotificationType.ANNOUNCEMENT,
        )
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
            client = form.save()
            _create_notification(
                "Client added",
                f"Client '{client.company_name}' was added.",
                NotificationType.ANNOUNCEMENT,
            )
            messages.success(request, "Client added.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    return redirect("hr:client_list")


def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save()
            _create_notification(
                "Client updated",
                f"Client '{client.company_name}' was updated.",
                NotificationType.ANNOUNCEMENT,
            )
            messages.success(request, "Client updated.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    return redirect("hr:client_list")


def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        company_name = client.company_name
        client.delete()
        _create_notification(
            "Client deleted",
            f"Client '{company_name}' was deleted.",
            NotificationType.ANNOUNCEMENT,
        )
        messages.success(request, "Client deleted.")
    return redirect("hr:client_list")


def reject_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = "Rejected"

    if request.user.is_authenticated:
        leave.approved_by = request.user

    leave.save()
    _create_notification(
        "Leave rejected",
        f"Leave request #{leave.pk} for {leave.user.get_full_name() or leave.user.username} was rejected.",
        NotificationType.LEAVE,
    )
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
            category = form.save()
            _create_notification(
                "Leave category added",
                f"Leave category '{category.name}' was added.",
                NotificationType.LEAVE,
            )
            messages.success(request, "Leave category added.")
            return redirect("hr:leave_dashboard")
    else:
        form = LeaveCategoryForm()

    return render(request, "hr/leave_category_form.html", {"form": form})


# =====================
# EVENTS
# =====================


def events_view(request):
    today = timezone.localdate()
    try:
        _send_event_reminders_if_due()
    except Exception:
        # Reminders should never block opening the calendar page.
        pass
    month_str = request.GET.get("month", "")
    try:
        current_month = date.fromisoformat(f"{month_str}-01") if month_str else today.replace(day=1)
    except ValueError:
        current_month = today.replace(day=1)

    first_weekday_mon0, days_in_month = monthrange(current_month.year, current_month.month)
    leading = (first_weekday_mon0 + 1) % 7
    grid_start = current_month - timedelta(days=leading)
    total_cells = 42
    grid_end = grid_start + timedelta(days=total_cells - 1)

    events_qs = Event.objects.filter(event_date__gte=grid_start, event_date__lte=grid_end).order_by("event_date", "start_time")
    events_by_date = {}
    for ev in events_qs:
        events_by_date.setdefault(ev.event_date, []).append(ev)

    def event_classes(ev):
        if ev.event_type == "MEETING":
            return "bg-primary", "badge bg-primary-subtle text-primary"
        if ev.event_type == "HOLIDAY":
            return "bg-success", "badge bg-success-subtle text-success"
        if ev.event_type == "BIRTHDAY":
            return "bg-warning", "badge bg-warning-subtle text-warning"
        return "bg-secondary", "badge bg-secondary-subtle text-secondary"

    days = []
    for i in range(total_cells):
        d = grid_start + timedelta(days=i)
        evs = events_by_date.get(d, [])
        first_dot_class = None
        ev_items = []
        if evs:
            dot_class, _ = event_classes(evs[0])
            first_dot_class = dot_class
            for e in evs:
                _, badge_class = event_classes(e)
                ev_items.append({
                    "title": e.title,
                    "badge_class": badge_class,
                })
        days.append({
            "date": d,
            "day": d.day,
            "is_muted": d.month != current_month.month,
            "events": ev_items,
            "first_event_dot_class": first_dot_class,
        })

    form = EventForm()
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user if request.user.is_authenticated else None
            obj.save()
            _create_notification(
                "Event created",
                f"Event '{obj.title}' was scheduled for {obj.event_date}.",
                NotificationType.EVENT,
            )
            messages.success(request, "Event created successfully.")
            return redirect("hr:events")
        else:
            messages.error(request, "Please correct the errors in the form.")

    context = {
        "form": form,
        "events": Event.objects.order_by("event_date", "start_time"),
        "days": days,
        "current_month_label": current_month.strftime("%B %Y"),
    }
    return render(request, "hr/events.html", context)


def delete_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        event_title = event.title
        event.delete()
        _create_notification(
            "Event deleted",
            f"Event '{event_title}' was deleted.",
            NotificationType.EVENT,
        )
        messages.success(request, "Event deleted.")
    return redirect("hr:events")

def event_detail(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    return render(request, "hr/event_detail.html", {"event": ev})

def event_edit(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        form = EventForm(request.POST, instance=ev)
        if form.is_valid():
            ev = form.save()
            _create_notification(
                "Event updated",
                f"Event '{ev.title}' was updated.",
                NotificationType.EVENT,
            )
            messages.success(request, "Event updated.")
            return redirect("hr:events")
        else:
            messages.error(request, "Please correct the errors in the form.")
            form = EventForm(request.POST, instance=ev)
    else:
        form = EventForm(instance=ev)
    return render(request, "hr/event_form.html", {"form": form, "event": ev, "is_edit": True})

def event_ics(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    content = _build_ics(ev)
    resp = HttpResponse(content, content_type="text/calendar")
    resp["Content-Disposition"] = f'attachment; filename="event-{ev.pk}.ics"'
    return resp

def send_event_reminders(request):
    try:
        _send_event_reminders_if_due()
    except Exception:
        messages.error(request, "Could not process reminders right now.")
        return redirect("hr:events")
    _create_notification(
        "Event reminders processed",
        "Event reminder dispatch was executed.",
        NotificationType.EVENT,
    )
    return redirect("hr:events")

def _build_ics(ev: Event) -> str:
    dtstart = f"{ev.event_date.strftime('%Y%m%d')}T{ev.start_time.strftime('%H%M%S')}"
    dtend = f"{ev.event_date.strftime('%Y%m%d')}T{(ev.end_time or ev.start_time).strftime('%H%M%S')}"
    summary = ev.title.replace('\n', ' ')
    description = (ev.description or '').replace('\n', '\\n')
    uid = f"hr-event-{ev.pk}@hr-portal"
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//HR Portal//Events//EN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{timezone.now().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines)

def _send_event_reminders_if_due():
    today = timezone.localdate()
    qs = Event.objects.filter(reminder_enabled=True, reminder_date=today, reminder_sent=False)
    for ev in qs:
        recipient = getattr(ev.created_by, "email", None)
        if recipient:
            subject = f"Reminder: {ev.title} on {ev.event_date}"
            body = (
                f"Event: {ev.title}\n"
                f"Date: {ev.event_date}\n"
                f"Time: {ev.start_time}" + (f" - {ev.end_time}" if ev.end_time else "") + "\n"
                f"Shared with: {ev.share_with}\n\n"
                f"Description:\n{ev.description or ''}"
            )
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
            try:
                send_mail(subject, body, from_email, [recipient], fail_silently=True)
                ev.reminder_sent = True
                ev.save(update_fields=["reminder_sent"])
            except Exception:
                pass

# =====================
# PERSONAL & TOOLS (simple pages rendered from templates)
# =====================

def notes_list_view(request):
    q = request.GET.get("q", "").strip()
    tag = request.GET.get("tag", "").strip()
    visibility = request.GET.get("visibility", "").strip().upper()

    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            notes = Note.objects.all()
        else:
            notes = Note.objects.filter(
                Q(visibility=NoteVisibility.SHARED) |
                Q(created_by_id=request.user.id)
            )
    else:
        notes = Note.objects.all()

    if q:
        notes = notes.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if tag:
        notes = notes.filter(tags__icontains=tag)
    if visibility in dict(NoteVisibility.choices):
        notes = notes.filter(visibility=visibility)

    notes_display = []
    for n in notes:
        tags_list = [t.strip() for t in (n.tags or "").split(",") if t.strip()]
        notes_display.append({"note": n, "tags": tags_list})
    form = NoteForm()
    return render(
        request,
        "hr/notes.html",
        {
            "notes": notes,
            "notes_display": notes_display,
            "notes_count": notes.count(),
            "q": q,
            "tag": tag,
            "visibility": visibility,
            "form": form,
        },
    )

def timeline_view(request):
    posts = TimelinePost.objects.select_related("created_by").prefetch_related("likes", "comments")
    post_form = TimelinePostForm()
    return render(request, "hr/timeline.html", {"posts": posts, "post_form": post_form})

def create_post_view(request):
    if request.method != "POST":
        return redirect("hr:timeline")
    form = TimelinePostForm(request.POST, request.FILES)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user if request.user.is_authenticated else None
        obj.save()
        _create_notification(
            "New timeline post",
            f"A new timeline post '{obj.title or obj.message[:40]}' was shared.",
            NotificationType.TIMELINE,
        )
        messages.success(request, "Post shared.")
    else:
        messages.error(request, "Please correct the errors in the post form.")
    return redirect("hr:timeline")

def like_post_view(request, pk):
    post = get_object_or_404(TimelinePost, pk=pk)
    if request.user.is_authenticated:
        TimelineLike.objects.get_or_create(post=post, user=request.user)
    else:
        TimelineLike.objects.create(post=post, user=None)
    return redirect("hr:timeline")

def comment_post_view(request, pk):
    post = get_object_or_404(TimelinePost, pk=pk)
    if request.method == "POST":
        form = TimelineCommentForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.post = post
            c.user = request.user if request.user.is_authenticated else None
            c.save()
            _create_notification(
                "New timeline comment",
                f"A comment was added on timeline post '{post.title or post.message[:40]}'.",
                NotificationType.TIMELINE,
            )
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Please enter a valid comment.")
    return redirect("hr:timeline")

def view_post_view(request, pk):
    TimelinePost.objects.filter(pk=pk).update(view_count=F("view_count") + 1)
    return redirect("hr:timeline")

def delete_post_view(request, pk):
    post = get_object_or_404(TimelinePost, pk=pk)
    if request.method == "POST":
        post_title = post.title or post.message[:40]
        post.delete()
        _create_notification(
            "Timeline post deleted",
            f"Timeline post '{post_title}' was deleted.",
            NotificationType.TIMELINE,
        )
        messages.success(request, "Post deleted.")
    return redirect("hr:timeline")

def help_list_view(request):
    articles = HelpArticle.objects.select_related("category").filter(is_active=True).order_by("-created_at")
    categories = HelpCategory.objects.all().order_by("name")
    form = HelpArticleForm()
    return render(request, "hr/help.html", {
        "articles": articles,
        "articles_count": articles.count(),
        "categories": categories,
        "form": form,
        "editing": False,
        "selected_category": None,
    })

def help_create_view(request):
    if request.method != "POST":
        return redirect("hr:help")
    form = HelpArticleForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user if request.user.is_authenticated else None
        obj.save()
        _create_notification(
            "Help article created",
            f"Help article '{obj.title}' was created.",
            NotificationType.ANNOUNCEMENT,
        )
        messages.success(request, "Help article created.")
    else:
        messages.error(request, "Please correct the errors in the article form.")
    return redirect("hr:help")

def help_detail_view(request, pk):
    article = get_object_or_404(HelpArticle, pk=pk, is_active=True)
    return render(request, "hr/help_detail.html", {"article": article})

def help_update_view(request, pk):
    article = get_object_or_404(HelpArticle, pk=pk)
    if request.method == "POST":
        form = HelpArticleForm(request.POST, instance=article)
        if form.is_valid():
            article = form.save()
            _create_notification(
                "Help article updated",
                f"Help article '{article.title}' was updated.",
                NotificationType.ANNOUNCEMENT,
            )
            messages.success(request, "Article updated successfully.")
            return redirect("hr:help")
    else:
        form = HelpArticleForm(instance=article)
    articles = HelpArticle.objects.select_related("category").filter(is_active=True).order_by("-created_at")
    categories = HelpCategory.objects.all().order_by("name")
    return render(request, "hr/help.html", {
        "articles": articles,
        "articles_count": articles.count(),
        "categories": categories,
        "form": form,
        "editing": True,
        "edit_article_id": article.pk,
    })

from django.views.decorators.http import require_POST

@require_POST
def help_delete_view(request, pk):
    article = get_object_or_404(HelpArticle, pk=pk)
    article_title = article.title
    article.delete()
    _create_notification(
        "Help article deleted",
        f"Help article '{article_title}' was deleted.",
        NotificationType.ANNOUNCEMENT,
    )
    messages.success(request, "Article deleted successfully.")
    return redirect("hr:help")

def category_filter_view(request, slug):
    category = get_object_or_404(HelpCategory, slug=slug)
    articles = HelpArticle.objects.select_related("category").filter(category=category, is_active=True).order_by("-created_at")
    categories = HelpCategory.objects.all().order_by("name")
    form = HelpArticleForm()
    return render(request, "hr/help.html", {
        "articles": articles,
        "articles_count": articles.count(),
        "categories": categories,
        "form": form,
        "selected_category": category,
        "editing": False,
    })

def todo_list_view(request):
    tasks = PersonalTask.objects.all().order_by("is_completed", "due_date", "-created_at")
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(is_completed=True).count()
    pending_tasks = total_tasks - completed_tasks
    completion_rate = round((completed_tasks / total_tasks) * 100, 1) if total_tasks else 0
    pending_rate = 100 - completion_rate if total_tasks else 0
    today = timezone.localdate()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    tasks_due_today = tasks.filter(due_date=today, is_completed=False).count()
    tasks_due_this_week = tasks.filter(due_date__range=(start_week, end_week), is_completed=False).count()
    context = {
        "tasks": tasks,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "completion_rate": completion_rate,
        "tasks_due_today": tasks_due_today,
        "tasks_due_this_week": tasks_due_this_week,
        "editing": False,
        "pending_rate": pending_rate,
    }
    return render(request, "hr/todo.html", context)

@require_POST
def add_task_view(request):
    form = PersonalTaskForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.user = User.objects.first()
        obj.save()
        _create_notification(
            "Personal task added",
            f"Personal to-do item '{obj.description}' was added.",
            NotificationType.TIMELINE,
        )
        messages.success(request, "Task added.")
    else:
        messages.error(request, "Please correct the errors in the form.")
    return redirect("hr:todo")

def edit_task_view(request, pk):
    task = get_object_or_404(PersonalTask, pk=pk)
    if request.method == "POST":
        form = PersonalTaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            _create_notification(
                "Personal task updated",
                f"Personal to-do item '{task.description}' was updated.",
                NotificationType.TIMELINE,
            )
            messages.success(request, "Task updated.")
            return redirect("hr:todo")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = PersonalTaskForm(instance=task)
    tasks = PersonalTask.objects.all().order_by("is_completed", "due_date", "-created_at")
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(is_completed=True).count()
    pending_tasks = total_tasks - completed_tasks
    completion_rate = round((completed_tasks / total_tasks) * 100, 1) if total_tasks else 0
    pending_rate = 100 - completion_rate if total_tasks else 0
    today = timezone.localdate()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    tasks_due_today = tasks.filter(due_date=today, is_completed=False).count()
    tasks_due_this_week = tasks.filter(due_date__range=(start_week, end_week), is_completed=False).count()
    return render(request, "hr/todo.html", {
        "tasks": tasks,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "completion_rate": completion_rate,
        "tasks_due_today": tasks_due_today,
        "tasks_due_this_week": tasks_due_this_week,
        "editing": True,
        "edit_task": task,
        "pending_rate": pending_rate,
    })

@require_POST
def delete_task_view(request, pk):
    task = get_object_or_404(PersonalTask, pk=pk)
    task_description = task.description
    task.delete()
    _create_notification(
        "Personal task deleted",
        f"Personal to-do item '{task_description}' was deleted.",
        NotificationType.TIMELINE,
    )
    messages.success(request, "Task deleted.")
    return redirect("hr:todo")

@require_POST
def toggle_task_status_view(request, pk):
    task = get_object_or_404(PersonalTask, pk=pk)
    task.is_completed = not task.is_completed
    task.save(update_fields=["is_completed"])
    _create_notification(
        "Personal task status changed",
        f"Personal to-do item '{task.description}' marked as {'completed' if task.is_completed else 'pending'}.",
        NotificationType.TIMELINE,
    )
    return redirect("hr:todo")

def notifications_view(request):
    all_notifications = Notification.objects.all().order_by("-created_at")
    selected_type = request.GET.get("type", "").strip().upper()
    valid_types = set(dict(NotificationType.choices).keys())
    notifications = all_notifications
    if selected_type in valid_types:
        notifications = notifications.filter(type=selected_type)
    else:
        selected_type = ""

    total_count = all_notifications.count()
    unread_count = all_notifications.filter(is_read=False).count()
    read_count = all_notifications.filter(is_read=True).count()
    type_counts = {
        "LEAVE": all_notifications.filter(type=NotificationType.LEAVE).count(),
        "ATTENDANCE": all_notifications.filter(type=NotificationType.ATTENDANCE).count(),
        "EVENT": all_notifications.filter(type=NotificationType.EVENT).count(),
        "ANNOUNCEMENT": all_notifications.filter(type=NotificationType.ANNOUNCEMENT).count(),
        "TIMELINE": all_notifications.filter(type=NotificationType.TIMELINE).count(),
        "SECURITY": all_notifications.filter(type=NotificationType.SECURITY).count(),
    }
    detail_urls = {
        "LEAVE": reverse("hr:leave_dashboard"),
        "ATTENDANCE": reverse("hr:attendance_list"),
        "EVENT": reverse("hr:events"),
        "ANNOUNCEMENT": reverse("hr:announcement_list"),
        "TIMELINE": reverse("hr:timeline"),
        "SECURITY": reverse("hr:settings"),
    }
    return render(
        request,
        "hr/notifications.html",
        {
            "notifications": notifications,
            "total_count": total_count,
            "unread_count": unread_count,
            "read_count": read_count,
            "type_counts": type_counts,
            "selected_type": selected_type,
            "detail_urls": detail_urls,
        },
    )


@require_POST
def mark_as_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect("hr:notifications")


@require_POST
def clear_notification_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    notification.delete()
    return redirect("hr:notifications")


@require_POST
def mark_all_read_view(request):
    Notification.objects.filter(is_read=False).update(is_read=True)
    return redirect("hr:notifications")


@require_POST
def clear_all_view(request):
    Notification.objects.all().delete()
    return redirect("hr:notifications")

def settings_view(request):
    profile = AdminProfile.objects.first()
    if profile is None:
        profile = AdminProfile.objects.create(
            full_name="HR Admin",
            email="hr.admin@company.com",
            role="HR",
            password=make_password("Admin@123"),
        )
    return render(request, "hr/settings.html", {"profile": profile})


@require_POST
def update_profile_view(request):
    profile = AdminProfile.objects.first()
    if profile is None:
        profile = AdminProfile.objects.create(
            full_name="HR Admin",
            email="hr.admin@company.com",
            role="HR",
            password=make_password("Admin@123"),
        )
    profile.full_name = request.POST.get("full_name", profile.full_name).strip() or profile.full_name
    profile.email = request.POST.get("email", profile.email).strip() or profile.email
    profile.save(update_fields=["full_name", "email"])
    return redirect("hr:settings")


@require_POST
def change_password_view(request):
    profile = AdminProfile.objects.first()
    if profile is None:
        profile = AdminProfile.objects.create(
            full_name="HR Admin",
            email="hr.admin@company.com",
            role="HR",
            password=make_password("Admin@123"),
        )

    new_password = request.POST.get("new_password", "")
    confirm_password = request.POST.get("confirm_password", "")

    is_valid = True
    if new_password != confirm_password:
        is_valid = False
    if len(new_password) < 8:
        is_valid = False
    if not re.search(r"[A-Z]", new_password):
        is_valid = False
    if not re.search(r"[a-z]", new_password):
        is_valid = False
    if not re.search(r"[0-9]", new_password):
        is_valid = False
    if not re.search(r"[^A-Za-z0-9]", new_password):
        is_valid = False

    if is_valid:
        profile.password = make_password(new_password)
        profile.save(update_fields=["password"])

    return redirect("hr:settings")

def note_create_view(request):
    if request.method == "POST":
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user if request.user.is_authenticated else None
            obj.save()
            _create_notification(
                "Note created",
                f"Note '{obj.title}' was created.",
                NotificationType.TIMELINE,
            )
            messages.success(request, "Note created.")
            return redirect("hr:notes")
        else:
            messages.error(request, "Please correct the errors in the form.")
            return redirect("hr:notes")
    form = NoteForm()
    return render(request, "hr/note_form.html", {"form": form, "is_edit": False})

def note_update_view(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if request.method == "POST":
        form = NoteForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            note = form.save()
            _create_notification(
                "Note updated",
                f"Note '{note.title}' was updated.",
                NotificationType.TIMELINE,
            )
            messages.success(request, "Note updated.")
            return redirect("hr:notes")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = NoteForm(instance=note)
    return render(request, "hr/note_form.html", {"form": form, "is_edit": True, "note": note})

def note_delete_view(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if request.method == "POST":
        note_title = note.title
        note.delete()
        _create_notification(
            "Note deleted",
            f"Note '{note_title}' was deleted.",
            NotificationType.TIMELINE,
        )
        messages.success(request, "Note deleted.")
        return redirect("hr:notes")
    return render(request, "hr/note_delete_confirm.html", {"note": note})

def note_detail_view(request, pk):
    note = get_object_or_404(Note, pk=pk)
    return render(request, "hr/note_detail.html", {"note": note})

def logout_view(request):
    logout(request)
    return redirect("accounts:login")
