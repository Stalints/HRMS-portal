from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.employee_login, name='employee_login'),
    path('dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('profile/', views.employee_profile, name='employee_profile'),
    path('leaves/', views.employee_leaves, name='employee_leaves'),
    

    path('tasks/', views.employee_tasks, name='employee_tasks'),
    path('attendance/', views.attendance_history, name='attendance_history'),
    path('announcements/', views.employee_announcements, name='employee_announcements'),

    path('clock-in/', views.clock_in, name='clock_in'),
    path('clock-out/', views.clock_out, name='clock_out'),
    
     path('events/', views.employee_events, name='employee_events'),
]
