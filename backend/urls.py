"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL configuration for backend project.
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from accounts.views_password import password_change_done_logout

# Redirect root URL to login page
def home_redirect(request):
    return redirect("login")


urlpatterns = [
    # Root → login
    path('', home_redirect, name="home_redirect"),

    # Admin
    path('admin/', admin.site.urls),

    # 🔐 Override password change form → custom template
    path(
        'accounts/password_change/',
        auth_views.PasswordChangeView.as_view(
            template_name='registration/password_change_form.html',
            success_url='/accounts/password_change/done/'
        ),
        name='password_change'
    ),

    # 🔐 Override password change done → auto logout
    path(
        'accounts/password_change/done/',
        password_change_done_logout,
        name='password_change_done'
    ),

    # Accounts → custom login/logout/signup (must come before built-in auth URLs)
    path('accounts/', include('accounts.urls')),

    # Built-in auth URLs → for password reset, etc.
    path('accounts/', include('django.contrib.auth.urls')),

    # Client module
    path('client/', include(('core.urls', 'core'), namespace='core')),

    # Employee module ✅ Add this
    path('employee/', include(('employee.urls', 'employee'), namespace='employee')),

    # HR module
    path('hr/', include(('hr.urls', 'hr'), namespace='hr')),

]



