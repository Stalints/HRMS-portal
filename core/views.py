from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import ClientProfile, Project, Invoice, Payment, Message, SupportTicket


# 🔒 Helper function: check CLIENT role
def is_client(user):
    return user.groups.filter(name="CLIENT").exists()


def get_client_profile(user):
    # auto-create profile if missing
    profile, _ = ClientProfile.objects.get_or_create(user=user)
    return profile


@login_required
def index(request):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)

    projects_count = Project.objects.filter(client=client).count()
    invoices_pending = Invoice.objects.filter(project__client=client, status="PENDING").count()
    tickets_open = SupportTicket.objects.filter(client=client, status="OPEN").count()
    unread_messages = Message.objects.filter(client=client, is_read=False).count()

    context = {
        "projects_count": projects_count,
        "invoices_pending": invoices_pending,
        "tickets_open": tickets_open,
        "unread_messages": unread_messages,
    }
    return render(request, "core/index.html", context)


@login_required
def projects(request):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)
    projects_qs = Project.objects.filter(client=client).order_by("-created_at")
    return render(request, "core/projects.html", {"projects": projects_qs})


@login_required
def project_create(request):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        status = request.POST.get("status", "PLANNED")

        start_date = request.POST.get("start_date") or None
        end_date = request.POST.get("end_date") or None

        if name:
            Project.objects.create(
                client=client,
                name=name,
                description=description,
                status=status,
                start_date=start_date,
                end_date=end_date,
            )

    return redirect("core:projects")



@login_required
def project_edit(request, pk):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)
    project = get_object_or_404(Project, id=pk, client=client)

    if request.method == "POST":
        project.name = request.POST.get("name", "").strip()
        project.description = request.POST.get("description", "").strip()
        project.status = request.POST.get("status", project.status)

        project.start_date = request.POST.get("start_date") or None
        project.end_date = request.POST.get("end_date") or None

        project.save()
        return redirect("core:projects")

    return render(request, "core/project_edit.html", {"project": project})


@login_required
def project_delete(request, pk):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)
    project = get_object_or_404(Project, id=pk, client=client)

    if request.method == "POST":
        project.delete()

    return redirect("core:projects")



# ✅ UPDATED: invoices view (shows invoices + provides projects for modal + handles POST create)
@login_required
def invoices(request):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)

    print("LOGGED USER:", request.user.username)

    # For modal dropdown
    projects_qs = Project.objects.filter(client=client).order_by("-created_at")

    # Create invoice from modal form
    if request.method == "POST":
        project_id = request.POST.get("project_id")
        amount = request.POST.get("amount")
        issued_date = request.POST.get("issued_date")
        due_date = request.POST.get("due_date") or None
        status = request.POST.get("status", "PENDING")

        project = get_object_or_404(Project, id=project_id, client=client)

        Invoice.objects.create(
            project=project,
            amount=amount,
            issued_date=issued_date,
            due_date=due_date,
            status=status
        )
        return redirect("core:invoices")

    invoices_qs = Invoice.objects.filter(project__client=client).order_by("-created_at")
    return render(request, "core/invoices.html", {"invoices": invoices_qs, "projects": projects_qs})


@login_required
def payments(request):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)
    payments_qs = Payment.objects.filter(invoice__project__client=client).order_by("-created_at")
    return render(request, "core/payments.html", {"payments": payments_qs})


@login_required
def messages(request):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)
    msgs = Message.objects.filter(client=client).order_by("-created_at")
    return render(request, "core/messages.html", {"messages": msgs})


@login_required
def profile(request):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)

    if request.method == "POST":
        client.company_name = request.POST.get("company_name", "")
        client.phone = request.POST.get("phone", "")
        client.address = request.POST.get("address", "")
        client.save()
        return redirect("core:profile")

    return render(request, "core/profile.html", {"client": client})


@login_required
def support(request):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        priority = request.POST.get("priority", "MEDIUM")

        if title and description:
            SupportTicket.objects.create(
                client=client,
                title=title,
                description=description,
                priority=priority
            )
        return redirect("core:support")

    tickets = SupportTicket.objects.filter(client=client).order_by("-created_at")
    return render(request, "core/support.html", {"tickets": tickets})


# ✅ Payment action (auto-save payment + mark invoice PAID)
@login_required
def pay_invoice(request, invoice_id):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)
    invoice = get_object_or_404(Invoice, id=invoice_id, project__client=client)

    if request.method == "POST":
        Payment.objects.create(
            invoice=invoice,
            amount_paid=invoice.amount,
            payment_date=timezone.now().date(),
            txn_id=request.POST.get("txn_id", "")
        )
        invoice.status = "PAID"
        invoice.save()
        return redirect("core:payments")

    return redirect("core:invoices")
