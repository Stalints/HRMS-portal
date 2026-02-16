from django.contrib import admin
from .models import EmployeeProfile, Leave, Task, Attendance, Announcement

admin.site.register(EmployeeProfile)
admin.site.register(Leave)
admin.site.register(Task)
admin.site.register(Attendance)
admin.site.register(Announcement)
