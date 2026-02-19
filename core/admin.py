from django.contrib import admin
from .models import ClientProfile, Project, Invoice, Payment, Message, SupportTicket

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "company_name")

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "client", "status")
    list_filter = ("status",)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "amount", "status", "issued_date")
    list_filter = ("status",)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice", "amount_paid", "payment_date")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "subject", "created_at")

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "title", "status", "priority")
    list_filter = ("status", "priority")


