from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountInfoViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="customer",
            password="test-password",
            first_name="Before",
            last_name="Customer",
            email="customer@example.com",
        )
        self.client.force_login(self.user)

    def test_account_field_can_be_updated_individually(self):
        response = self.client.post(
            reverse("account_info"),
            {"field": "first_name", "first_name": "After"},
        )

        self.assertRedirects(response, reverse("account_info"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "After")
        self.assertEqual(self.user.username, "customer")
        self.assertEqual(self.user.last_name, "Customer")
        self.assertEqual(self.user.email, "customer@example.com")
