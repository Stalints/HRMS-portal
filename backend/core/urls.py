from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('invoices/', views.invoices, name='invoices'),
    path('payments/', views.payments, name='payments'),
    path('messages/', views.messages, name='messages'),
    path('profile/', views.profile, name='profile'),
    path('projects/', views.projects, name='projects'),
    path('support/', views.support, name='support'),
]
