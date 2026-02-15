from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


# 🔒 Helper function: check CLIENT role
def is_client(user):
    return user.groups.filter(name="CLIENT").exists()


@login_required
def index(request):
    if not is_client(request.user):
        return redirect("login")
    return render(request, 'core/index.html')


@login_required
def invoices(request):
    if not is_client(request.user):
        return redirect("login")
    return render(request, 'core/invoices.html')


@login_required
def payments(request):
    if not is_client(request.user):
        return redirect("login")
    return render(request, 'core/payments.html')


@login_required
def messages(request):
    if not is_client(request.user):
        return redirect("login")
    return render(request, 'core/messages.html')


@login_required
def profile(request):
    if not is_client(request.user):
        return redirect("login")
    return render(request, 'core/profile.html')


@login_required
def projects(request):
    if not is_client(request.user):
        return redirect("login")
    return render(request, 'core/projects.html')


@login_required
def support(request):
    if not is_client(request.user):
        return redirect("login")
    return render(request, 'core/support.html')
