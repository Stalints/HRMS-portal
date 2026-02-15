from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views_password import password_change_done_logout
from .views_signup import hr_signup_view   # ✅ Add this import


urlpatterns = [
    # Custom login/logout views
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # HR Signup
    path("signup/hr/", hr_signup_view, name="hr_signup"),

    # Password change (custom template)
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change_form.html",
            success_url="/accounts/password_change/done/"
        ),
        name="password_change"
    ),

    # Password change done (custom view for auto logout)
    path(
        "password_change/done/",
        password_change_done_logout,
        name="password_change_done"
    ),

    path("logout/", views.logout_view, name="logout"),

]
