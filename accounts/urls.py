from django.contrib.auth import views as auth_views
from django.urls import path
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
  path("card/", views.create_setup_intent, name="card_info" )
]