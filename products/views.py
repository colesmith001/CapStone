from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from .models import Products

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