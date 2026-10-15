from django.db import models

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