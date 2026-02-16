from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views_password import password_change_done_logout
from .views_signup import hr_signup_view

app_name = "accounts"

urlpatterns = [
    # Authentication
   path("login/", views.login_view, name="login"),
   path("logout/", views.logout_view, name="logout"),
    
    # HR-specific signup
    path("signup/hr/", hr_signup_view, name="hr_signup"),
    
    # Password management
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change_form.html",
            success_url="/accounts/password/change/done/"
        ),
        name="password_change"
    ),
    path(
        "password/change/done/",
        password_change_done_logout,
        name="password_change_done"
    ),
]