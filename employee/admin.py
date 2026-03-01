from django.contrib import admin
from .models import Event, EmployeeProfile, Leave, Task, Attendance, Announcement

admin.site.register(EmployeeProfile)
admin.site.register(Event)
admin.site.register(Leave)
admin.site.register(Task)
admin.site.register(Attendance)
admin.site.register(Announcement)
