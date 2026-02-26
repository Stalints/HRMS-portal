from django.shortcuts import redirect
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.urls import reverse

def hr_signup_view(request):
    # If user opens /signup/hr/ directly, send them to combined login page
    if request.method != "POST":
        return redirect("login")

    username = (request.POST.get("username") or "").strip()
    email = (request.POST.get("email") or "").strip().lower()
    password = request.POST.get("password") or ""
    confirm_password = request.POST.get("confirm_password") or ""

    if not username:
        messages.error(request, "Username is required.")
        return redirect("login")

    if not email:
        messages.error(request, "Email is required.")
        return redirect("login")

    if password != confirm_password:
        messages.error(request, "Passwords do not match.")
        return redirect("login")

    if User.objects.filter(username=username).exists():
        messages.error(request, "Username already taken.")
        return redirect("login")

    if User.objects.filter(email=email).exists():
        messages.error(request, "Email already registered.")
        return redirect("login")

    user = User.objects.create_user(username=username, email=email, password=password)

    hr_group, _ = Group.objects.get_or_create(name="HR")
    user.groups.add(hr_group)

    messages.success(request, "HR account created successfully. Please login.")
    return redirect("login")