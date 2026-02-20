from django.urls import path
from . import views
from django.urls import path
from . import api_views

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

    path("api/profile/", api_views.profile_get, name="api_profile_get"),
    path("api/profile/update/", api_views.profile_update, name="api_profile_update"),
    path("api/profile/remove-photo/", api_views.profile_remove_photo, name="api_profile_remove_photo"),
]
