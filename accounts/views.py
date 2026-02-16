from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User


def login_view(request):
    # 🔁 Redirect if already logged in
    if request.user.is_authenticated:
        if request.user.groups.filter(name="HR").exists():
            return redirect("hr:dashboard")
        elif request.user.groups.filter(name="CLIENT").exists():
            return redirect("core:client_dashboard")
        elif request.user.groups.filter(name="EMPLOYEE").exists():
            return redirect("employee:employee_dashboard")

    if request.method == "POST":
        email = request.POST.get("email").lower()
        password = request.POST.get("password")
        role = request.POST.get("role").upper()

        # 🔹 Find first user by email
        user = User.objects.filter(email=email).first()
        if not user:
            messages.error(request, "Invalid email or password")
            return render(request, "registration/login.html")

        # ✅ Check role using GROUPS
        if not user.groups.filter(name=role).exists():
            messages.error(request, f"User is not assigned to role: {role}")
            return render(request, "registration/login.html")

        # 🔹 Authenticate using username internally
        user = authenticate(request, username=user.username, password=password)

        if user:
            is_first_login = user.last_login is None
            login(request, user)

            # 🔐 Force password change on first login
            if is_first_login:
                return redirect("/accounts/password_change/")

            # 🔁 Role-based redirect
            if role == "HR":
                return redirect("hr:dashboard")
            elif role == "CLIENT":
                return redirect("core:client_dashboard")
            elif role == "EMPLOYEE":
                return redirect("employee:employee_dashboard")

        messages.error(request, "Invalid email or password")

    return render(request, "registration/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")
