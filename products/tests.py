from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Cart, CartItem, Products


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


class CartTests(TestCase):
  def setUp(self):
    self.user = get_user_model().objects.create_user(
      username="customer",
      password="test-password",
    )
    self.product = Products.objects.create(
      name="Latte",
      description="Espresso with steamed milk.",
      category="Coffee",
      price="5.25",
    )
    self.client.force_login(self.user)

  def test_adding_product_increments_cart_item_quantity(self):
    url = reverse("add_to_cart", args=[self.product.pk])

    self.client.post(url)
    response = self.client.post(url)

    item = CartItem.objects.get(cart__user=self.user, product=self.product)
    self.assertEqual(response.status_code, 302)
    self.assertEqual(item.quantity, 2)

  def test_cart_displays_all_items_and_total(self):
    cart = Cart.objects.create(user=self.user)
    CartItem.objects.create(cart=cart, product=self.product, quantity=2)
    another_product = Products.objects.create(
      name="Muffin",
      category="Bakery",
      price="3.00",
    )
    CartItem.objects.create(cart=cart, product=another_product, quantity=1)

    response = self.client.get(reverse("cart_detail"))

    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "Latte")
    self.assertContains(response, "Muffin")
    self.assertContains(response, "$13.50")

  def test_removing_product_removes_it_from_cart(self):
    cart = Cart.objects.create(user=self.user)
    CartItem.objects.create(cart=cart, product=self.product, quantity=2)

    response = self.client.post(
      reverse("remove_from_cart", args=[self.product.pk])
    )

    self.assertEqual(response.status_code, 302)
    self.assertFalse(CartItem.objects.filter(cart=cart).exists())

  def test_cart_page_shows_empty_cart_for_new_user(self):
    response = self.client.get(reverse("cart_detail"))

    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "Your cart is empty.")
