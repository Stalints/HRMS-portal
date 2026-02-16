from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('team/', views.team_list, name='team_list'),
    path('team/add/', views.team_add, name='team_add'),
    path('team/edit/<int:pk>/', views.team_edit, name='team_edit'),
    path('team/activate/<int:pk>/', views.team_activate, name='team_activate'),
    path('team/deactivate/<int:pk>/', views.team_deactivate, name='team_deactivate'),

    path('attendance/', views.attendance_list, name='attendance_list'),

    path("leave/", views.leave_dashboard, name="leave_dashboard"),
    path("leave/approve/<int:pk>/", views.approve_leave, name="approve_leave"),
    path("leave/reject/<int:pk>/", views.reject_leave, name="reject_leave"),
    path("leave/category/add-ajax/", views.add_leave_category_ajax, name="add_leave_category_ajax"),
]
