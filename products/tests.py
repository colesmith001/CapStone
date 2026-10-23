from django.test import TestCase
from django.urls import reverse
from .models import Products


class ProductDetailTests(TestCase):
  def setUp(self):
    self.product = Products.objects.create(
      name="Cappuccino",
      description="Espresso with steamed milk.",
      category="Coffee",
      price="4.50",
    )

  def test_menu_card_links_to_product_detail(self):
    response = self.client.get(reverse("products_list"))

    self.assertContains(response, reverse("product_detail", args=[self.product.pk]))

  def test_product_detail_shows_product_information(self):
    response = self.client.get(reverse("product_detail", args=[self.product.pk]))

    self.assertEqual(response.status_code, 200)
    self.assertContains(response, self.product.name)
    self.assertContains(response, self.product.description)
    self.assertContains(response, self.product.category)
    self.assertContains(response, "$4.50")

  def test_unavailable_product_detail_returns_404(self):
    self.product.is_available = False
    self.product.save()

    response = self.client.get(reverse("product_detail", args=[self.product.pk]))

    self.assertEqual(response.status_code, 404)
