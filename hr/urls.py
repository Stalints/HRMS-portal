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
    path("leave/category/add/", views.add_leave_category, name="add_leave_category"),

    path("announcements/", views.announcement_list, name="announcement_list"),
    path("announcements/<int:pk>/edit/", views.announcement_edit, name="announcement_edit"),
    path("announcements/<int:pk>/delete/", views.announcement_delete, name="announcement_delete"),

    path("projects/", views.project_list, name="project_list"),
    path("projects/add/", views.project_create, name="project_create"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/edit/", views.project_update, name="project_update"),
    path("projects/<int:pk>/delete/", views.project_delete, name="project_delete"),

    path("tasks/", views.task_list, name="task_list"),
    path("tasks/add/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/edit/", views.task_update, name="task_update"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),

    path("clients/", views.client_list, name="client_list"),
    path("clients/add/", views.client_create, name="client_create"),
    path("clients/<int:pk>/edit/", views.client_update, name="client_update"),
    path("clients/<int:pk>/delete/", views.client_delete, name="client_delete"),

    path("clients/events/", views.client_events, name="client_events"),

]
