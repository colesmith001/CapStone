from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views


urlpatterns = [
  path('signup/', views.signup_view, name='signup'),
  path(
    'login/',
    auth_views.LoginView.as_view(
      template_name='accounts/login.html',
    ),
    name='login',
  ),
  path(
    'logout/',
    views.logout_view,
    name='logout',
  ),
  path("profile/", views.account_info_view, name="account_info"),
  path("card/", views.card_page, name="card_page"),
  path(
    "card/setup-intent/",
    views.create_setup_intent,
    name="create_setup_intent",
  ),
  path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),

  path(
    "password-reset/",
    auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset_form.html",
        email_template_name="accounts/password_reset_email.txt",
        subject_template_name="accounts/password_reset_subject.txt",
        success_url=reverse_lazy("password_reset_done"),
    ),
    name="password_reset",
),
path(
    "password-reset/done/",
    auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html",
    ),
    name="password_reset_done",
),
path(
    "reset/<uidb64>/<token>/",
    auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        success_url=reverse_lazy("password_reset_complete"),
    ),
    name="password_reset_confirm",
),
path(
    "reset/done/",
    auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html",
    ),
    name="password_reset_complete",
),
]