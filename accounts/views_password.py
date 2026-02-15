from django.contrib.auth import logout
from django.shortcuts import redirect

def password_change_done_logout(request):
    logout(request)
    return redirect("login")
