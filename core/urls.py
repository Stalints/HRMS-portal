from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="client_dashboard"),
    path("dashboard/", views.index, name="dashboard"),

    path("invoices/", views.invoices, name="invoices"),
    path("invoices/<int:invoice_id>/pay/", views.pay_invoice, name="pay_invoice"),  # old flow (keep)

    path("payments/", views.payments, name="payments"),
    path("payments/create/", views.payment_create, name="payment_create"),
    path("payments/<int:pk>/pay/", views.payment_pay_now, name="payment_pay_now"),
    path("payments/<int:pk>/delete/", views.payment_delete, name="payment_delete"),

    path("invoice/pay-now/", views.invoice_pay_now, name="invoice_pay_now"),  # ✅ ajax endpoint

    path("messages/", views.messages, name="messages"),
    path("profile/", views.profile, name="profile"),

    path("projects/", views.projects, name="projects"),
    path("projects/create/", views.project_create, name="project_create"),
    path("projects/<int:pk>/edit/", views.project_edit, name="project_edit"),
    path("projects/<int:pk>/delete/", views.project_delete, name="project_delete"),

    path("support/", views.support, name="support"),
]
