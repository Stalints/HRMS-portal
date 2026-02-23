from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Sum
from django.core.files.storage import default_storage

from .models import (
    ClientProfile, Project, Invoice, Payment, Message, SupportTicket,
    PaymentStatus, PaymentMethod
)

from hr.models import Event
from django.db.models import Q
from django.utils import timezone

from datetime import date, timedelta
from calendar import monthrange

from hr.models import Event  



def is_client(user):
    return user.groups.filter(name="CLIENT").exists()


def get_client_profile(user):
    profile, _ = ClientProfile.objects.get_or_create(user=user)
    return profile


# -------------------------
# ✅ PROFILE API (Traditional Django JSON)
# -------------------------
def client_profile_to_dict(p):
    return {
        "full_name": p.full_name,
        "email": p.user.email,
        "phone": p.phone,
        "company": p.company,
        "address": p.address,
        "profile_image": p.profile_image.url if p.profile_image else None,
        "client_id": p.client_id,
        "member_since": p.member_since,
        "is_active": p.is_active,
    }


@login_required
@require_GET
def api_profile_get(request):
    if not is_client(request.user):
        return JsonResponse({"ok": False, "message": "Not allowed"}, status=403)

    p = get_client_profile(request.user)
    return JsonResponse(client_profile_to_dict(p), status=200)


@login_required
@require_POST
def api_profile_update(request):
    if not is_client(request.user):
        return JsonResponse({"ok": False, "message": "Not allowed"}, status=403)

    p = get_client_profile(request.user)

    # normal fields (partial update)
    if "full_name" in request.POST:
        p.full_name = request.POST.get("full_name", "").strip()

    if "phone" in request.POST:
        p.phone = request.POST.get("phone", "").strip()

    if "company" in request.POST:
        p.company = request.POST.get("company", "").strip()

    if "address" in request.POST:
        p.address = request.POST.get("address", "").strip()

    # update Django auth user email (your UI has Email)
    if "email" in request.POST:
        email = request.POST.get("email", "").strip()
        if email:
            request.user.email = email
            request.user.save(update_fields=["email"])

    # profile image upload (same endpoint)
    if "profile_image" in request.FILES:
        # delete old image file if exists
        if p.profile_image and default_storage.exists(p.profile_image.name):
            default_storage.delete(p.profile_image.name)

        p.profile_image = request.FILES["profile_image"]

    p.save()

    return JsonResponse({"ok": True, "data": client_profile_to_dict(p)}, status=200)


@login_required
@require_POST
def api_profile_remove_photo(request):
    if not is_client(request.user):
        return JsonResponse({"ok": False, "message": "Not allowed"}, status=403)

    p = get_client_profile(request.user)

    if p.profile_image:
        if default_storage.exists(p.profile_image.name):
            default_storage.delete(p.profile_image.name)
        p.profile_image = None
        p.save(update_fields=["profile_image"])

    return JsonResponse({"ok": True}, status=200)


# -------------------------
# CLIENT PAGES
# -------------------------
@login_required
def index(request):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)

    projects_count = Project.objects.filter(client=client).count()
    invoices_pending = Invoice.objects.filter(project__client=client, status="PENDING").count()
    tickets_open = SupportTicket.objects.filter(client=client, status="OPEN").count()
    unread_messages = Message.objects.filter(client=client, is_read=False).count()

    return render(request, "core/index.html", {
        "projects_count": projects_count,
        "invoices_pending": invoices_pending,
        "tickets_open": tickets_open,
        "unread_messages": unread_messages,
    })


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


@login_required
def invoices(request):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)
    projects_qs = Project.objects.filter(client=client).order_by("-created_at")

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

    payments_qs = Payment.objects.filter(
        invoice__project__client=client
    ).select_related("invoice", "invoice__project").order_by("-created_at")

    invoices_qs = Invoice.objects.filter(
        project__client=client
    ).select_related("project").order_by("-created_at")

    total_paid = payments_qs.filter(status=PaymentStatus.COMPLETED).aggregate(s=Sum("amount_paid"))["s"] or 0
    pending = payments_qs.filter(status=PaymentStatus.PENDING).aggregate(s=Sum("amount_paid"))["s"] or 0

    last_payment = payments_qs.filter(status=PaymentStatus.COMPLETED).order_by("-payment_date", "-created_at").first()

    return render(request, "core/payments.html", {
        "payments": payments_qs,
        "invoices": invoices_qs,
        "total_paid": total_paid,
        "pending": pending,
        "last_payment": last_payment,
    })


@login_required
@require_POST
def payment_create(request):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)

    invoice_id = request.POST.get("invoice_id")
    payment_id = (request.POST.get("payment_id") or "").strip()
    amount_paid = request.POST.get("amount_paid") or 0
    payment_date = request.POST.get("payment_date") or timezone.now().date()

    invoice = get_object_or_404(Invoice, id=invoice_id, project__client=client)

    Payment.objects.create(
        invoice=invoice,
        payment_id=payment_id,
        amount_paid=amount_paid,
        payment_date=payment_date,
        status=PaymentStatus.PENDING,
    )
    return redirect("core:payments")


@login_required
@require_POST
def payment_pay_now(request, pk):
    if not is_client(request.user):
        return JsonResponse({"ok": False, "message": "Not allowed"}, status=403)

    client = get_client_profile(request.user)
    payment = get_object_or_404(Payment, pk=pk, invoice__project__client=client)

    method = request.POST.get("method")

    if method not in [PaymentMethod.CARD, PaymentMethod.UPI, PaymentMethod.BANK]:
        return JsonResponse({"ok": False, "message": "Invalid method"}, status=400)

    if method == PaymentMethod.CARD:
        card_number = (request.POST.get("card_number") or "").strip().replace(" ", "")
        card_expiry = (request.POST.get("card_expiry") or "").strip()
        card_cvv = (request.POST.get("card_cvv") or "").strip()

        if len(card_number) < 12 or not card_number.isdigit():
            return JsonResponse({"ok": False, "message": "Enter a valid card number."}, status=400)
        if not card_expiry:
            return JsonResponse({"ok": False, "message": "Enter card expiry (MM/YY)."}, status=400)
        if len(card_cvv) < 3 or not card_cvv.isdigit():
            return JsonResponse({"ok": False, "message": "Enter valid CVV."}, status=400)

        payment.card_last4 = card_number[-4:]

    elif method == PaymentMethod.UPI:
        upi_id = (request.POST.get("upi_id") or "").strip()
        upi_pin = (request.POST.get("upi_pin") or "").strip()

        if not upi_id or "@" not in upi_id:
            return JsonResponse({"ok": False, "message": "Enter valid UPI ID (example@bank)."}, status=400)
        if len(upi_pin) < 4 or not upi_pin.isdigit():
            return JsonResponse({"ok": False, "message": "Enter valid UPI PIN."}, status=400)

        payment.upi_id = upi_id

    else:  # BANK
        bank_ref = (request.POST.get("bank_ref") or "").strip()
        if not bank_ref:
            return JsonResponse({"ok": False, "message": "Enter bank reference number."}, status=400)

        payment.bank_ref = bank_ref

    payment.method = method
    payment.status = PaymentStatus.COMPLETED
    payment.txn_id = f"DUMMY-{payment.payment_id}"
    payment.save()

    payment.invoice.status = "PAID"
    payment.invoice.save()

    return JsonResponse({"ok": True, "message": "Payment successful (dummy)."})


@login_required
@require_POST
def invoice_pay_now(request):
    if not is_client(request.user):
        return JsonResponse({"ok": False, "message": "Not allowed"}, status=403)

    client = get_client_profile(request.user)

    invoice_id = request.POST.get("invoice_id")
    if not invoice_id:
        return JsonResponse({"ok": False, "message": "Invoice id missing."}, status=400)

    invoice = get_object_or_404(Invoice, id=invoice_id, project__client=client)

    method = request.POST.get("method")
    if method not in [PaymentMethod.CARD, PaymentMethod.UPI, PaymentMethod.BANK]:
        return JsonResponse({"ok": False, "message": "Invalid method"}, status=400)

    if method == PaymentMethod.CARD:
        card_number = (request.POST.get("card_number") or "").strip().replace(" ", "")
        card_expiry = (request.POST.get("card_expiry") or "").strip()
        card_cvv = (request.POST.get("card_cvv") or "").strip()

        if len(card_number) < 12 or not card_number.isdigit():
            return JsonResponse({"ok": False, "message": "Enter a valid card number."}, status=400)
        if not card_expiry:
            return JsonResponse({"ok": False, "message": "Enter card expiry (MM/YY)."}, status=400)
        if len(card_cvv) < 3 or not card_cvv.isdigit():
            return JsonResponse({"ok": False, "message": "Enter valid CVV."}, status=400)

        last4 = card_number[-4:]
        upi_id = ""
        bank_ref = ""

    elif method == PaymentMethod.UPI:
        upi_id = (request.POST.get("upi_id") or "").strip()
        upi_pin = (request.POST.get("upi_pin") or "").strip()

        if not upi_id or "@" not in upi_id:
            return JsonResponse({"ok": False, "message": "Enter valid UPI ID (example@bank)."}, status=400)
        if len(upi_pin) < 4 or not upi_pin.isdigit():
            return JsonResponse({"ok": False, "message": "Enter valid UPI PIN."}, status=400)

        last4 = ""
        bank_ref = ""

    else:  # BANK
        bank_ref = (request.POST.get("bank_ref") or "").strip()
        if not bank_ref:
            return JsonResponse({"ok": False, "message": "Enter bank reference number."}, status=400)

        last4 = ""
        upi_id = ""

    Payment.objects.create(
        invoice=invoice,
        payment_id=f"PAY-INV-{invoice.id}-{int(timezone.now().timestamp())}",
        amount_paid=invoice.amount,
        payment_date=timezone.now().date(),
        status=PaymentStatus.COMPLETED,
        method=method,
        txn_id=f"DUMMY-INV-{invoice.id}",
        card_last4=(last4 or ""),
        upi_id=(upi_id or ""),
        bank_ref=(bank_ref or ""),
    )

    invoice.status = "PAID"
    invoice.save()

    return JsonResponse({"ok": True, "message": f"Invoice INV-{invoice.id} paid successfully (dummy)."})


@login_required
@require_POST
def payment_delete(request, pk):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)

    payment = get_object_or_404(
        Payment,
        pk=pk,
        invoice__project__client=client
    )
    payment.delete()
    return redirect("core:payments")


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

    # ✅ only render the template (your JS will call the API endpoints)
    return render(request, "core/profile.html")


@login_required
def support(request):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        priority = request.POST.get("priority", "MEDIUM")
        category = request.POST.get("category", "LOGIN")

        if title and description:
            SupportTicket.objects.create(
                client=client,
                title=title,
                description=description,
                priority=priority,
                category=category
            )
        return redirect("core:support")

    tickets = SupportTicket.objects.filter(client=client).order_by("-created_at")
    return render(request, "core/support.html", {"tickets": tickets})


@login_required
def pay_invoice(request, invoice_id):
    if not is_client(request.user):
        return redirect("login")

    client = get_client_profile(request.user)
    invoice = get_object_or_404(Invoice, id=invoice_id, project__client=client)

    if request.method == "POST":
        Payment.objects.create(
            invoice=invoice,
            payment_id=f"PAY-{invoice.id}-{int(timezone.now().timestamp())}",
            amount_paid=invoice.amount,
            payment_date=timezone.now().date(),
            status=PaymentStatus.COMPLETED,
            method=PaymentMethod.BANK,
            txn_id=request.POST.get("txn_id", "")
        )
        invoice.status = "PAID"
        invoice.save()
        return redirect("core:payments")

    return redirect("core:invoices")




@login_required
def client_events(request):
    # Only clients can view this page
    if not is_client(request.user):
        return redirect("login")

    return render(request, "core/events.html")


@login_required
@require_GET
def client_events_api(request):
    # Only clients can load events
    if not is_client(request.user):
        return JsonResponse({"error": "Not allowed"}, status=403)

    # Client sees only Client / All events
    qs = Event.objects.filter(
        Q(share_with__icontains="Client") | Q(share_with__icontains="All")
    ).order_by("event_date", "start_time")

    events = []
    for ev in qs:
        # FullCalendar expects ISO date-time strings
        start_dt = timezone.make_aware(
            timezone.datetime.combine(ev.event_date, ev.start_time)
        )

        if ev.end_time:
            end_dt = timezone.make_aware(
                timezone.datetime.combine(ev.event_date, ev.end_time)
            )
        else:
            end_dt = None

        events.append({
            "id": ev.id,
            "title": ev.title,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat() if end_dt else None,
            "extendedProps": {
                "description": ev.description or "",
                "share_with": ev.share_with,
                "event_type": ev.event_type,
                "date": ev.event_date.strftime("%d %b %Y"),
                "start_time": ev.start_time.strftime("%H:%M"),
                "end_time": ev.end_time.strftime("%H:%M") if ev.end_time else "",
            }
        })

    return JsonResponse(events, safe=False)


@login_required
def knowledge_base(request):
    return render(request, "core/knowledge_base.html")



   