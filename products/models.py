from django.db import models
from django.conf import settings
from decimal import Decimal

# Create your models here.
class Products(models.Model):
  name = models.CharField(max_length=120)
  description = models.TextField(blank=True)
  category = models.CharField(max_length=80)
  price = models.DecimalField(max_digits=8, decimal_places = 2)
  image = models.ImageField(upload_to='products/', blank=True)
  is_available = models.BooleanField(default=True)

  def __str__(self):
        return self.name

class Cart(models.Model):
  user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="cart",
  )
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  @property
  def total(self):
    return sum(
      (item.line_total for item in self.items.all()),
      start=Decimal("0.00")
    )
  

class CartItem(models.Model):
  cart = models.ForeignKey(
    Cart,
    on_delete=models.CASCADE,
    related_name="items",
  )
  product = models.ForeignKey(
    Products,
    on_delete=models.PROTECT,
  )
  quantity = models.PositiveIntegerField(default=1)

  class Meta:
    constraints = [
      models.UniqueConstraint(
        fields=["cart", "product"],
        name="one_cart_item_per_product",
      )
    ]

  @property
  def line_total(self):
    return self.product.price * self.quantity

    
    