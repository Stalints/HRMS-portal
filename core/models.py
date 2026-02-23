from django.db import models
from django.conf import settings
from django.utils import timezone
from django.conf import settings
from django.db import models


class ClientProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_profile"
    )

    full_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    company = models.CharField(max_length=150, blank=True)
    address = models.TextField(blank=True)

    # profile picture
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)

    is_active = models.BooleanField(default=True)

    # Auto ID like CL-1023
    client_id = models.CharField(max_length=20, unique=True, blank=True)

    # ✅ FIX: avoid migration asking default when table already has rows
    member_since = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Auto-generate client_id only if empty
        if not self.client_id:
            last = ClientProfile.objects.exclude(client_id="").order_by("-id").first()

            if last and last.client_id.startswith("CL-"):
                try:
                    last_num = int(last.client_id.split("-")[1])
                except Exception:
                    last_num = 1022
                next_num = last_num + 1
            else:
                next_num = 1023

            self.client_id = f"CL-{next_num}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - ClientProfile"


class Project(models.Model):
    STATUS_CHOICES = [
        ("PLANNED", "Planned"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("ON_HOLD", "On Hold"),
    ]

    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="PLANNED")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("OVERDUE", "Overdue"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="invoices")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.id} - {self.project.name}"


# -------------------------
# PAYMENTS (UPDATED FOR DUMMY PAY NOW FLOW)
# -------------------------

class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    COMPLETED = "COMPLETED", "Completed"


class PaymentMethod(models.TextChoices):
    CARD = "CARD", "Credit Card"
    UPI = "UPI", "UPI"
    BANK = "BANK", "Bank Transfer"


class Payment(models.Model):
    # link to invoice
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")

    # for UI like PAY-201 (unique)
    payment_id = models.CharField(max_length=50, unique=True)

    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)

    method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.UPI)
    status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    # dummy “transaction id”
    txn_id = models.CharField(max_length=100, blank=True)

    # dummy method-specific saved values
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    upi_id = models.CharField(max_length=120, blank=True, null=True)
    bank_ref = models.CharField(max_length=120, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.payment_id} - Invoice #{self.invoice.id} - {self.status}"


class Message(models.Model):
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name="messages")
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("RESOLVED", "Resolved"),
    ]

    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    ]

    CATEGORY_CHOICES = [
        ("LOGIN", "Login"),
        ("INVOICE", "Invoice"),
        ("PAYMENT", "Payment"),
        ("PROJECT", "Project"),
    ]

    ticket_id = models.CharField(max_length=20, unique=True, blank=True)
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name="tickets")
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            import random
            self.ticket_id = f"SUP-{random.randint(10000, 99999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.title}"

