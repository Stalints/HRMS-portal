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
    is_online = models.BooleanField(default=False)

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
    
    # New Fields
    employees = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="assigned_projects")
    progress_percentage = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Milestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=200)
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Task(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
    ]
    
    RECURRING_CHOICES = [
        ("NONE", "None"),
        ("DAILY", "Daily"),
        ("WEEKLY", "Weekly"),
        ("MONTHLY", "Monthly"),
        ("YEARLY", "Yearly"),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True
    )
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    
    PRIORITY_CHOICES = [
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="Medium")
    
    # Document attachments
    attachment = models.FileField(upload_to="task_files/", blank=True, null=True)
    recurring = models.CharField(max_length=20, choices=RECURRING_CHOICES, default="NONE")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on task {self.task.title}"

class Invoice(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("OVERDUE", "Overdue"),
        ("PARTIAL", "Partial"),
    ]

    invoice_number = models.CharField(max_length=30, unique=True, blank=True)
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name="invoices_direct", null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="invoices")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_1_name = models.CharField(max_length=50, blank=True)
    tax_1_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_2_name = models.CharField(max_length=50, blank=True)
    tax_2_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_3_name = models.CharField(max_length=50, blank=True)
    tax_3_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    issued_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            import random
            random_num = random.randint(1000, 9999)
            self.invoice_number = f"INV-{random_num}"
        super().save(*args, **kwargs)

    @property
    def get_tax_amounts(self):
        t1 = (self.amount * self.tax_1_percentage) / 100
        t2 = (self.amount * self.tax_2_percentage) / 100
        t3 = (self.amount * self.tax_3_percentage) / 100
        return t1, t2, t3

    @property
    def total_tax(self):
        t1, t2, t3 = self.get_tax_amounts
        return t1 + t2 + t3
        
    @property
    def total_amount(self):
        return self.amount + self.total_tax

    def refresh_payment_status(self):
        paid_total = self.payments.aggregate(total=models.Sum("amount_paid"))["total"] or 0
        
        if paid_total >= self.total_amount and self.total_amount > 0:
            new_status = "PAID"
        elif paid_total > 0:
            new_status = "PARTIAL"
        else:
            new_status = "PENDING"

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=["status"])

    def __str__(self):
        return f"{self.invoice_number} - {self.project.name if self.project else 'Invoice'}"

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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.refresh_payment_status()

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        super().delete(*args, **kwargs)
        invoice.refresh_payment_status()

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
        ("IN_PROGRESS", "In Progress"),
        ("CLOSED", "Closed"),
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
    
    # HR assigns to employee
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")

    related_task = models.ForeignKey(
        "Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_ticket",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            import random
            self.ticket_id = f"SUP-{random.randint(10000, 99999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.title}"

class TicketComment(models.Model):
    SEND_TO_CHOICES = [
        ("CLIENT", "Client"),
        ("EMPLOYEE", "Assigned Employee"),
    ]
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField()
    send_to = models.CharField(
        max_length=20,
        choices=SEND_TO_CHOICES,
        default="CLIENT",
        help_text="Who can see this comment: Client or Assigned Employee.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on ticket {self.ticket.ticket_id}"

class TimeCard(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='timecards')
    date = models.DateField(default=timezone.now)
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0, editable=False)

    def save(self, *args, **kwargs):
        if self.clock_in and self.clock_out:
            delta = self.clock_out - self.clock_in
            self.total_hours = round(delta.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.username} - {self.date}"
