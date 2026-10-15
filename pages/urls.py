from django.urls import path
from pages import views

urlpatterns = [
  path('',views.about_view, name = 'about'),
  
]