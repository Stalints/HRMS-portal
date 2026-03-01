from django.urls import path
from . import views

app_name = "employee"   # ⭐ IMPORTANT

urlpatterns = [
    path('login/', views.employee_login, name='employee_login'),
    path('logout/', views.employee_logout, name='employee_logout'),
    
    path('dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('profile/', views.employee_profile, name='employee_profile'),
    path('leaves/', views.employee_leaves, name='employee_leaves'),

    path('tasks/', views.employee_tasks, name='employee_tasks'),
    path('attendance/', views.attendance_history, name='attendance_history'),
    path('announcements/', views.employee_announcements, name='employee_announcements'),

    path('clock-in/', views.clock_in, name='clock_in'),
    path('clock-out/', views.clock_out, name='clock_out'),

    path('events/', views.employee_events, name='employee_events'),

    path('chat/', views.chat_dashboard, name='chat_dashboard'),
    path('chat/<int:pk>/', views.chat_room, name='chat_room'),
    path('chat/start/<int:user_id>/', views.chat_start, name='chat_start'),
    path('chat/delete/<int:pk>/', views.chat_delete, name='chat_delete'),

    path('todo/', views.employee_todo_list_view, name='employee_todo_list'),
    path('todo/create/', views.employee_todo_create_view, name='employee_todo_create'),
    path('todo/<int:pk>/update/', views.employee_todo_update_view, name='employee_todo_update'),
    path('todo/<int:pk>/delete/', views.employee_todo_delete_view, name='employee_todo_delete'),
    path('todo/<int:pk>/toggle/', views.employee_todo_toggle_status_view, name='employee_todo_toggle'),
]