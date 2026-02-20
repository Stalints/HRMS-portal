from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('team/', views.employee_list, name='employee_list'),
    path('team/add/', views.employee_add, name='employee_add'),
    path('team/edit/<int:pk>/', views.employee_edit, name='employee_edit'),
    path('team/activate/<int:pk>/', views.employee_activate, name='employee_activate'),
    path('team/deactivate/<int:pk>/', views.employee_deactivate, name='employee_deactivate'),
    path('teams/', views.team_list, name='team_list'),
    path('teams/add/', views.team_create, name='team_add'),
    path('teams/<int:pk>/', views.team_detail, name='team_detail'),
    path('teams/<int:pk>/edit/', views.team_update, name='team_edit'),
    path('teams/<int:pk>/delete/', views.team_delete, name='team_delete'),

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

    path("events/", views.events_view, name="events"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("events/<int:pk>/edit/", views.event_edit, name="event_edit"),
    path("events/delete/<int:pk>/", views.delete_event, name="delete_event"),
    path("events/<int:pk>/ics/", views.event_ics, name="event_ics"),
    path("events/reminders/send/", views.send_event_reminders, name="send_event_reminders"),

    # Personal & Tools - Notes
    path("notes/", views.notes_list_view, name="notes"),
    path("notes/add/", views.note_create_view, name="note_add"),
    path("notes/<int:pk>/", views.note_detail_view, name="note_detail"),
    path("notes/<int:pk>/edit/", views.note_update_view, name="note_edit"),
    path("notes/<int:pk>/delete/", views.note_delete_view, name="note_delete"),
    path("timeline/", views.timeline_view, name="timeline"),
    path("timeline/add/", views.create_post_view, name="add_post"),
    path("timeline/<int:pk>/like/", views.like_post_view, name="like_post"),
    path("timeline/<int:pk>/comment/", views.comment_post_view, name="comment_post"),
    path("timeline/<int:pk>/view/", views.view_post_view, name="view_post"),
    path("timeline/<int:pk>/delete/", views.delete_post_view, name="delete_post"),
    path("help/", views.help_list_view, name="help"),
    path("help/add/", views.help_create_view, name="help_create"),
    path("help/<int:pk>/", views.help_detail_view, name="help_detail"),
    path("help/<int:pk>/edit/", views.help_update_view, name="help_edit"),
    path("help/<int:pk>/delete/", views.help_delete_view, name="help_delete"),
    path("help/category/<slug:slug>/", views.category_filter_view, name="category_filter"),
    path("todo/", views.todo_list_view, name="todo"),
    path("todo/add/", views.add_task_view, name="add_task"),
    path("todo/<int:pk>/edit/", views.edit_task_view, name="edit_task"),
    path("todo/<int:pk>/delete/", views.delete_task_view, name="delete_task"),
    path("todo/<int:pk>/toggle/", views.toggle_task_status_view, name="toggle_task_status"),
    path("notifications/", views.notifications, name="notifications"),
    path("settings/", views.settings_page, name="settings"),
]

