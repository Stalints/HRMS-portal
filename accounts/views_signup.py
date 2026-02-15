from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib import messages

def hr_signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email").lower()  # normalize email
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Password match check
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "registration/hr_signup.html")

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "registration/hr_signup.html")

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)

        # Assign HR group
        hr_group, created = Group.objects.get_or_create(name="HR")
        user.groups.add(hr_group)

        messages.success(request, "HR account created successfully. Please login.")
        return redirect("login")

    return render(request, "registration/hr_signup.html")
