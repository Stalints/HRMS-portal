from django.shortcuts import render


def index(request):
    return render(request, 'core/index.html')

def invoices(request):
    return render(request, 'core/invoices.html')

def payments(request):
    return render(request, 'core/payments.html')

def messages(request):
    return render(request, 'core/messages.html')

def profile(request):
    return render(request, 'core/profile.html')

def projects(request):
    return render(request, 'core/projects.html')

def support(request):
    return render(request, 'core/support.html')

# Create your views here.
