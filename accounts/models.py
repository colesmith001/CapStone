from django.conf import settings
from django.db import models

# Create your models here.

class UserProfile(models.Model):
  user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="profile"
  )
  picture = models.ImageField(
    upload_to="profile_pictures/",
    blank=True,
    null=True,
  )
  user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="profile"
  )
  picture = models.ImageField(
    upload_to="profile_pictures/",
    blank=True,
    null=True,
  )

  stripe_customer_id= models.CharField(max_length=255, blank=True)
  defualt_payment_method_id= models.CharField(max_length=255, blank=True)
  card_brand = models.CharField(max_length=30, blank=True)
  card_last4 = models.CharField(max_length=4, blank=True)

  def __str__(self):
    return f"{self.user.username}'s profile"