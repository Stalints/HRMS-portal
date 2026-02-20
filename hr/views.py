from datetime import date, timedelta
from calendar import monthrange

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q, F
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    AttendanceForm, TeamMemberAddForm, TeamMemberEditForm,
    AnnouncementForm, ProjectForm, TaskForm, ClientForm,
    LeaveCategoryForm, EventForm, NoteForm,
    TimelinePostForm, TimelineCommentForm,
    HelpArticleForm, PersonalTaskForm
)

from .models import (
    Attendance, LeaveRequest, LeaveCategory,
    Announcement, AnnouncementStatus,
    Project, Task, TaskStatus,
    Client,
    Event,
    Note, NoteVisibility,
    TimelinePost, TimelineLike, TimelineComment,
    HelpArticle, HelpCategory,
    PersonalTask
)


from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import PersonalTask
from .forms import PersonalTaskForm


User = get_user_model()


# =====================
# GROUP HELPERS (Auth User + Groups)
# =====================

def _is_in_group(user, group_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=group_name).exists()

def _is_hr(user) -> bool:
    # allow staff as HR (optional)
    return _is_in_group(user, "HR") or (user.is_authenticated and user.is_staff)

def _is_employee(user) -> bool:
    return _is_in_group(user, "EMPLOYEE")

def _is_client(user) -> bool:
    return _is_in_group(user, "CLIENT")


def _hr_required(view_func):
    """Only HR (or staff) can access these pages."""
    @login_required(login_url="hr:login")
    def _wrapped(request, *args, **kwargs):
        if not _is_hr(request.user):
            messages.error(request, "You are not allowed to access HR pages.")
            # Change redirect if you have separate dashboards
            return redirect("hr:dashboard")
        return view_func(request, *args, **kwargs)
    return _wrapped


# =====================
# DASHBOARD
# =====================

@login_required(login_url="hr:login")
def dashboard(request):
    active_announcements = (
        Announcement.objects
        .filter(status=AnnouncementStatus.ACTIVE)
        .order_by("-publish_date", "-created_at")[:5]
    )

    today = timezone.localdate()
    upcoming = Event.objects.filter(event_date__gte=today).order_by("event_date", "start_time")[:5]

    # Employee sees only Employee/Team events
    if _is_employee(request.user):
        upcoming = upcoming.filter(Q(share_with__icontains="Employee") | Q(share_with__icontains="Team"))

    # Client sees only Client/All events (optional - depends on your data)
    if _is_client(request.user):
        upcoming = upcoming.filter(Q(share_with__icontains="Client") | Q(share_with__icontains="All"))

    # HR sees all

    return render(request, "hr/dashboard.html", {
        "active_announcements": active_announcements,
        "active_announcements_count": active_announcements.count(),
        "upcoming_events": upcoming,
    })


# =====================
# TEAM MANAGEMENT (HR ONLY)
# =====================

@_hr_required
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


@_hr_required
def team_add(request):
    if request.method == "POST":
        form = TeamMemberAddForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Team member added successfully.")
            return redirect("hr:team_list")
    else:
        form = TeamMemberAddForm()

    return render(request, "hr/team_form.html", {"form": form, "is_edit": False})


@_hr_required
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


@_hr_required
def team_activate(request, pk):
    member = get_object_or_404(User, pk=pk)
    member.is_active = True
    member.save(update_fields=["is_active"])
    messages.success(request, f"{member.get_full_name()} activated.")
    return redirect("hr:team_list")


@_hr_required
def team_deactivate(request, pk):
    member = get_object_or_404(User, pk=pk)
    member.is_active = False
    member.save(update_fields=["is_active"])
    messages.success(request, f"{member.get_full_name()} deactivated.")
    return redirect("hr:team_list")


# =====================
# ATTENDANCE (HR ONLY)
# =====================

@_hr_required
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
            return redirect(f"{reverse('hr:attendance_list')}?date={obj.date.isoformat()}")
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
        "total_employees": User.objects.filter(is_active=True).count(),
        "present_today": records.filter(status="PRESENT").count(),
        "absent_today": records.filter(status="ABSENT").count(),
        "late_today": records.filter(status="LATE").count(),
    }
    return render(request, "hr/attendance.html", context)


# =====================
# LEAVE MANAGEMENT (HR ONLY)
# =====================

@_hr_required
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


@_hr_required
def approve_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = "Approved"
    leave.approved_by = request.user
    leave.save()
    messages.success(request, "Leave approved.")
    return redirect("hr:leave_dashboard")


@_hr_required
def reject_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = "Rejected"
    leave.approved_by = request.user
    leave.save()
    messages.success(request, "Leave rejected.")
    return redirect("hr:leave_dashboard")


@_hr_required
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


# =====================
# ANNOUNCEMENTS (HR ONLY)
# =====================

@_hr_required
def announcement_list(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.created_by = request.user
            ann.save()
            messages.success(request, "Announcement created.")
            return redirect("hr:announcement_list")
    else:
        form = AnnouncementForm()

    announcements = Announcement.objects.all().order_by("-publish_date", "-created_at")
    return render(request, "hr/announcements.html", {"form": form, "announcements": announcements})


@_hr_required
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


@_hr_required
def announcement_delete(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        ann.delete()
        messages.success(request, "Announcement deleted.")
        return redirect("hr:announcement_list")
    return render(request, "hr/announcement_delete_confirm.html", {"announcement": ann})


# =====================
# PROJECTS (HR ONLY)
# =====================

@_hr_required
def project_list(request):
    projects = Project.objects.all()
    return render(request, "hr/projects.html", {"projects": projects})


@_hr_required
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


@_hr_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, "hr/project_detail.html", {"project": project})


@_hr_required
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


@_hr_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        project.delete()
        messages.success(request, "Project deleted.")
        return redirect("hr:project_list")
    return render(request, "hr/project_delete_confirm.html", {"project": project})


# =====================
# TASKS (HR ONLY)
# =====================

@_hr_required
def task_list(request):
    status_filter = request.GET.get("status")
    tasks = Task.objects.select_related("project").all()
    if status_filter in dict(TaskStatus.choices).keys():
        tasks = tasks.filter(status=status_filter)
    form = TaskForm()
    return render(request, "hr/tasks.html", {"tasks": tasks, "form": form, "status_filter": status_filter})


@_hr_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Task created.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    return redirect("hr:task_list")


@_hr_required
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


@_hr_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted.")
    return redirect("hr:task_list")


# =====================
# CLIENTS (HR ONLY)
# =====================

@_hr_required
def client_list(request):
    clients = Client.objects.all()
    form = ClientForm()
    return render(request, "hr/clients.html", {"clients": clients, "form": form})


@_hr_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Client added.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    return redirect("hr:client_list")


@_hr_required
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


@_hr_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        client.delete()
        messages.success(request, "Client deleted.")
    return redirect("hr:client_list")


# =====================
# EVENTS (ALL LOGGED-IN USERS, filtered by group)
# =====================

@login_required(login_url="hr:login")
def events_view(request):
    today = timezone.localdate()
    _send_event_reminders_if_due()

    month_str = request.GET.get("month", "")
    try:
        current_month = date.fromisoformat(f"{month_str}-01") if month_str else today.replace(day=1)
    except ValueError:
        current_month = today.replace(day=1)

    first_weekday_mon0, _days_in_month = monthrange(current_month.year, current_month.month)
    leading = (first_weekday_mon0 + 1) % 7
    grid_start = current_month - timedelta(days=leading)
    total_cells = 42
    grid_end = grid_start + timedelta(days=total_cells - 1)

    events_qs = Event.objects.filter(event_date__gte=grid_start, event_date__lte=grid_end).order_by("event_date", "start_time")

    # Group filters
    if _is_employee(request.user):
        events_qs = events_qs.filter(Q(share_with__icontains="Employee") | Q(share_with__icontains="Team"))
    elif _is_client(request.user):
        events_qs = events_qs.filter(Q(share_with__icontains="Client") | Q(share_with__icontains="All"))
    # HR sees all

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
                ev_items.append({"title": e.title, "badge_class": badge_class})
        days.append({
            "date": d,
            "day": d.day,
            "is_muted": d.month != current_month.month,
            "events": ev_items,
            "first_event_dot_class": first_dot_class,
        })

    # Only HR can create events (optional; if you want everyone, remove this check)
    if request.method == "POST":
        if not _is_hr(request.user):
            messages.error(request, "Only HR can create events.")
            return redirect("hr:events")

        form = EventForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Event created successfully.")
            return redirect("hr:events")
        messages.error(request, "Please correct the errors in the form.")

    form = EventForm()

    context = {
        "form": form,
        "events": events_qs.order_by("event_date", "start_time"),
        "days": days,
        "current_month_label": current_month.strftime("%B %Y"),
    }
    return render(request, "hr/events.html", context)


@_hr_required
def delete_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        event.delete()
        messages.success(request, "Event deleted.")
    return redirect("hr:events")


@login_required(login_url="hr:login")
def event_detail(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    return render(request, "hr/event_detail.html", {"event": ev})


@_hr_required
def event_edit(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        form = EventForm(request.POST, instance=ev)
        if form.is_valid():
            form.save()
            messages.success(request, "Event updated.")
            return redirect("hr:events")
        messages.error(request, "Please correct the errors in the form.")
    else:
        form = EventForm(instance=ev)

    return render(request, "hr/event_form.html", {"form": form, "event": ev, "is_edit": True})


@login_required(login_url="hr:login")
def event_ics(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    content = _build_ics(ev)
    resp = HttpResponse(content, content_type="text/calendar")
    resp["Content-Disposition"] = f'attachment; filename="event-{ev.pk}.ics"'
    return resp


@_hr_required
def send_event_reminders(request):
    _send_event_reminders_if_due()
    return redirect("hr:events")


def _build_ics(ev: Event) -> str:
    dtstart = f"{ev.event_date.strftime('%Y%m%d')}T{ev.start_time.strftime('%H%M%S')}"
    dtend = f"{ev.event_date.strftime('%Y%m%d')}T{(ev.end_time or ev.start_time).strftime('%H%M%S')}"
    summary = (ev.title or "").replace("\n", " ")
    description = (ev.description or "").replace("\n", "\\n")
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
            send_mail(subject, body, from_email, [recipient], fail_silently=True)
            ev.reminder_sent = True
            ev.save(update_fields=["reminder_sent"])

            


# =====================
# NOTES (All logged-in, permissions applied)
# =====================

@login_required(login_url="hr:login")
def notes_list_view(request):
    q = request.GET.get("q", "").strip()
    tag = request.GET.get("tag", "").strip()
    visibility = request.GET.get("visibility", "").strip().upper()

    if _is_hr(request.user):
        notes = Note.objects.all()
    else:
        notes = Note.objects.filter(Q(visibility=NoteVisibility.SHARED) | Q(created_by_id=request.user.id))

    if q:
        notes = notes.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if tag:
        notes = notes.filter(tags__icontains=tag)
    if visibility in dict(NoteVisibility.choices):
        notes = notes.filter(visibility=visibility)

    notes_display = []
    for n in notes.order_by("-created_at"):
        tags_list = [t.strip() for t in (n.tags or "").split(",") if t.strip()]
        notes_display.append({"note": n, "tags": tags_list})

    form = NoteForm()
    return render(request, "hr/notes.html", {
        "notes": notes,
        "notes_display": notes_display,
        "notes_count": notes.count(),
        "q": q,
        "tag": tag,
        "visibility": visibility,
        "form": form,
    })


@login_required(login_url="hr:login")
def note_create_view(request):
    if request.method == "POST":
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Note created.")
        else:
            messages.error(request, "Please correct the errors in the form.")
        return redirect("hr:notes")

    form = NoteForm()
    return render(request, "hr/note_form.html", {"form": form, "is_edit": False})


@login_required(login_url="hr:login")
def note_update_view(request, pk):
    note = get_object_or_404(Note, pk=pk)

    if not _is_hr(request.user) and note.created_by_id != request.user.id:
        messages.error(request, "You are not allowed to edit this note.")
        return redirect("hr:notes")

    if request.method == "POST":
        form = NoteForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, "Note updated.")
            return redirect("hr:notes")
        messages.error(request, "Please correct the errors in the form.")
    else:
        form = NoteForm(instance=note)

    return render(request, "hr/note_form.html", {"form": form, "is_edit": True, "note": note})


@login_required(login_url="hr:login")
def note_delete_view(request, pk):
    note = get_object_or_404(Note, pk=pk)

    if not _is_hr(request.user) and note.created_by_id != request.user.id:
        messages.error(request, "You are not allowed to delete this note.")
        return redirect("hr:notes")

    if request.method == "POST":
        note.delete()
        messages.success(request, "Note deleted.")
        return redirect("hr:notes")
    return render(request, "hr/note_delete_confirm.html", {"note": note})


@login_required(login_url="hr:login")
def note_detail_view(request, pk):
    note = get_object_or_404(Note, pk=pk)

    if not _is_hr(request.user):
        if note.visibility != NoteVisibility.SHARED and note.created_by_id != request.user.id:
            messages.error(request, "You are not allowed to view this note.")
            return redirect("hr:notes")

    return render(request, "hr/note_detail.html", {"note": note})


# =====================
# TIMELINE (All logged-in)
# =====================

@login_required(login_url="hr:login")
def timeline_view(request):
    posts = TimelinePost.objects.select_related("created_by").prefetch_related("likes", "comments").order_by("-created_at")
    post_form = TimelinePostForm()
    return render(request, "hr/timeline.html", {"posts": posts, "post_form": post_form})


@login_required(login_url="hr:login")
def add_post(request):
    if request.method != "POST":
        return redirect("hr:timeline")
    form = TimelinePostForm(request.POST, request.FILES)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        messages.success(request, "Post shared.")
    else:
        messages.error(request, "Please correct the errors in the post form.")
    return redirect("hr:timeline")


@login_required(login_url="hr:login")
def like_post_view(request, pk):
    post = get_object_or_404(TimelinePost, pk=pk)
    TimelineLike.objects.get_or_create(post=post, user=request.user)
    return redirect("hr:timeline")


@login_required(login_url="hr:login")
def comment_post_view(request, pk):
    post = get_object_or_404(TimelinePost, pk=pk)
    if request.method == "POST":
        form = TimelineCommentForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.post = post
            c.user = request.user
            c.save()
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Please enter a valid comment.")
    return redirect("hr:timeline")


@login_required(login_url="hr:login")
def view_post_view(request, pk):
    TimelinePost.objects.filter(pk=pk).update(view_count=F("view_count") + 1)
    return redirect("hr:timeline")


@_hr_required
def delete_post_view(request, pk):
    post = get_object_or_404(TimelinePost, pk=pk)
    if request.method == "POST":
        post.delete()
        messages.success(request, "Post deleted.")
    return redirect("hr:timeline")


# =====================
# HELP (All logged-in; create/update/delete = HR only)
# =====================

@login_required(login_url="hr:login")
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


@_hr_required
def help_create_view(request):
    if request.method != "POST":
        return redirect("hr:help")
    form = HelpArticleForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        messages.success(request, "Help article created.")
    else:
        messages.error(request, "Please correct the errors in the article form.")
    return redirect("hr:help")


@login_required(login_url="hr:login")
def help_detail_view(request, pk):
    article = get_object_or_404(HelpArticle, pk=pk, is_active=True)
    return render(request, "hr/help_detail.html", {"article": article})


@_hr_required
def help_update_view(request, pk):
    article = get_object_or_404(HelpArticle, pk=pk)
    if request.method == "POST":
        form = HelpArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
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


@require_POST
@_hr_required
def help_delete_view(request, pk):
    article = get_object_or_404(HelpArticle, pk=pk)
    article.delete()
    messages.success(request, "Article deleted successfully.")
    return redirect("hr:help")


@login_required(login_url="hr:login")
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


# =====================
# TODO (Personal - only own tasks)
# =====================

@login_required(login_url="hr:login")
def todo_list_view(request):
    tasks = PersonalTask.objects.filter(user=request.user).order_by("is_completed", "due_date", "-created_at")
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
@login_required(login_url="hr:login")
def add_task_view(request):
    form = PersonalTaskForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        messages.success(request, "Task added.")
    else:
        messages.error(request, "Please correct the errors in the form.")
    return redirect("hr:todo")


@login_required(login_url="hr:login")
def edit_task_view(request, pk):
    task = get_object_or_404(PersonalTask, pk=pk, user=request.user)
    if request.method == "POST":
        form = PersonalTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated.")
            return redirect("hr:todo")
        messages.error(request, "Please correct the errors in the form.")
    else:
        form = PersonalTaskForm(instance=task)

    tasks = PersonalTask.objects.filter(user=request.user).order_by("is_completed", "due_date", "-created_at")
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
@login_required(login_url="hr:login")
def delete_task_view(request, pk):
    task = get_object_or_404(PersonalTask, pk=pk, user=request.user)
    task.delete()
    messages.success(request, "Task deleted.")
    return redirect("hr:todo")


@require_POST
@login_required(login_url="hr:login")
def toggle_task_status_view(request, pk):
    task = get_object_or_404(PersonalTask, pk=pk, user=request.user)
    task.is_completed = not task.is_completed
    task.save(update_fields=["is_completed"])
    return redirect("hr:todo")


# =====================
# SIMPLE PAGES
# =====================

@login_required(login_url="hr:login")
def notifications(request):
    return render(request, "hr/notifications.html")


@login_required(login_url="hr:login")
def settings_page(request):
    return render(request, "hr/settings.html")


# =====================
# AUTH
# =====================

def login_view(request):
    if request.user.is_authenticated:
        return redirect("hr:dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next")
            return redirect(next_url or "hr:dashboard")

        messages.error(request, "Invalid username or password.")

    return render(request, "hr/login.html")


@login_required(login_url="hr:login")
def logout_view(request):
    logout(request)
    return redirect("hr:login")
  
            

# --------- SIMPLE PAGES (PLACEHOLDERS) ----------

def client_events(request):
    return render(request, "hr/clients/events.html")

def events(request):
    return render(request, "hr/events.html")

def send_event_reminders(request):
    return render(request, "hr/events_reminders.html")


def notes(request):
    return render(request, "hr/notes.html")

def note_add(request):
    return render(request, "hr/notes/form.html")

def note_detail(request, pk):
    return render(request, "hr/notes/detail.html", {"pk": pk})

def note_edit(request, pk):
    return render(request, "hr/notes/form.html", {"pk": pk})

def note_delete(request, pk):
    return render(request, "hr/notes/delete.html", {"pk": pk})


def timeline(request):
    return render(request, "hr/timeline.html")

def add_post(request):
    return render(request, "hr/timeline_add_post.html")


def notifications(request):
    return render(request, "hr/notifications.html")



def help_page(request):
    return render(request, "hr/help.html")
from django.shortcuts import render, redirect

def help_create(request):
    # later you will save form here
    return redirect("hr:help")

def help_edit(request, pk):
    # later you will load + update article here
    return redirect("hr:help")

def help_delete(request, pk):
    # later you will delete article here
    return redirect("hr:help")



def settings_page(request):
    return render(request, "hr/settings.html")

def todo(request):
    return render(request, "hr/todo.html")

def add_task(request):
    return redirect("hr:todo")

def edit_task(request, pk):
    return redirect("hr:todo")

def delete_task(request, pk):
    return redirect("hr:todo")

def toggle_task(request, pk):
    return redirect("hr:todo")                 