from django.urls import path
from . import views

# Required for template namespacing
app_name = 'core'

urlpatterns = [
    path('dashboard/', views.index, name='client_dashboard'),
    path('invoices/', views.invoices, name='invoices'),
    path('payments/', views.payments, name='payments'),
    path('messages/', views.messages, name='messages'),
    path('profile/', views.profile, name='profile'),
    path('projects/', views.projects, name='projects'),
    path('support/', views.support, name='support'),
]
