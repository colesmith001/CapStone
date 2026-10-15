from django.db.models import Q
from django.shortcuts import render
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