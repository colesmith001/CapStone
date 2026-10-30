from django.urls import path
from . import views

urlpatterns = [
  path('', views.product_list, name='products_list'),
  path("cart/", views.cart_detail, name="cart_detail"),
  path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
  path("cart/remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
  path('<int:product_id>/', views.product_detail, name='product_detail'),
]