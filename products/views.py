from decimal import Decimal
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Cart, CartItem, Products

# Create your views here.
def product_list(request):
  query = request.GET.get('q','').strip()

  products = Products.objects.filter(is_available=True)

  if query:
      products = products.filter(
        Q(name__icontains=query)
        | Q(description__icontains=query)
        | Q(category__icontains=query)
      )

  return render(request, "products/products_list.html", {
    "products": products,
    "query": query,
})


def product_detail(request, product_id):
  product = get_object_or_404(Products, pk=product_id, is_available=True)
  return render(request, "products/product_detail.html", {
    "product": product,
  })

MAX_QUANTITY_PER_ADD = 99

@login_required
@require_POST
def add_to_cart(request, product_id):
  product = get_object_or_404(
    Products,
    pk=product_id,
    is_available=True
  ) 

  try:
    quantity = int(request.POST.get("quantity", 1))
  except ValueError:
    quantity = 0

  if quantity < 1 or quantity > MAX_QUANTITY_PER_ADD:
    messages.error(request, "Please enter a quantity between 1 and {MAX_QUANTITY_PER_ADD}")
    return redirect("product_detail", product_id=product_id)


  cart, _ = Cart.objects.get_or_create(user=request.user)
  item, created = CartItem.objects.get_or_create(
    cart=cart,
    product=product,
    defaults={"quantity": quantity},
  )
  if not created:
    CartItem.objects.filter(pk=item.pk).update(
      quantity=F("quantity") + quantity)

  return redirect("cart_detail")

@login_required
def cart_detail(request):
  cart = Cart.objects.filter(user=request.user).first()
  items = list(cart.items.select_related("product")) if cart else []
  total = sum((item.line_total for item in items), start=Decimal("0.00"))

  return render(request, "products/cart.html", {
    "items": items,
    "total": total,
  })

@require_POST
@login_required
def remove_from_cart(request, product_id):
  CartItem.objects.filter(
    cart__user=request.user,
    product_id=product_id,
  ).delete()
  return redirect("cart_detail")