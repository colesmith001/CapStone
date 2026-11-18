from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
import stripe

from .models import UserProfile


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

    def test_account_page_shows_card_status_and_manage_link(self):
        profile = UserProfile.objects.get(user=self.user)
        profile.card_brand = "visa"
        profile.card_last4 = "4242"
        profile.save(update_fields=["card_brand", "card_last4"])

        response = self.client.get(reverse("account_info"))

        self.assertContains(response, "Visa")
        self.assertContains(response, "4242")
        self.assertContains(response, reverse("card_page"))


class StripeCardSetupTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="stripe-customer",
            password="test-password",
            email="stripe-customer@example.com",
        )
        self.client.force_login(self.user)

    def test_card_page_renders_stripe_form(self):
        with self.settings(STRIPE_PUBLISHABLE_KEY="pk_test_example"):
            response = self.client.get(reverse("card_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Save a card")
        self.assertContains(response, "pk_test_example")

    @patch("accounts.views.stripe.SetupIntent.create")
    @patch("accounts.views.stripe.Customer.create")
    def test_setup_intent_is_created_for_current_user(
        self,
        create_customer,
        create_setup_intent,
    ):
        create_customer.return_value = SimpleNamespace(id="cus_test")
        create_setup_intent.return_value = SimpleNamespace(
            client_secret="seti_secret_test"
        )

        with self.settings(
            STRIPE_SECRET_KEY="sk_test_example",
            STRIPE_PUBLISHABLE_KEY="pk_test_example",
        ):
            response = self.client.post(reverse("create_setup_intent"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"client_secret": "seti_secret_test"})
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.stripe_customer_id, "cus_test")
        create_setup_intent.assert_called_once_with(
            customer="cus_test",
            automatic_payment_methods={"enabled": True},
            usage="off_session",
        )

    @patch("accounts.views.stripe.Customer.create")
    def test_stripe_setup_error_shows_safe_diagnostic_in_debug(
        self,
        create_customer,
    ):
        create_customer.side_effect = stripe.StripeError(
            "Example Stripe error",
            code="example_error",
        )

        with self.settings(
            STRIPE_SECRET_KEY="sk_test_example",
            STRIPE_PUBLISHABLE_KEY="pk_test_example",
            DEBUG=True,
        ):
            response = self.client.post(reverse("create_setup_intent"))

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json(),
            {
                "error": (
                    "Stripe request failed: StripeError, "
                    "code=example_error, Example Stripe error"
                )
            },
        )

    @patch("accounts.views.stripe.SetupIntent.create")
    def test_invalid_setup_intent_shows_safe_parameter_diagnostic(
        self,
        create_setup_intent,
    ):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.stripe_customer_id = "cus_test"
        profile.save(update_fields=["stripe_customer_id"])
        create_setup_intent.side_effect = stripe.InvalidRequestError(
            "No such customer: cus_test123; key sk_test_example123",
            param="customer",
            code="resource_missing",
        )

        with self.settings(
            STRIPE_SECRET_KEY="sk_test_example",
            STRIPE_PUBLISHABLE_KEY="pk_test_example",
            DEBUG=True,
        ):
            response = self.client.post(reverse("create_setup_intent"))

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json(),
            {
                "error": (
                    "Stripe request failed: InvalidRequestError, "
                    "code=resource_missing, param=customer, No such customer: "
                    "[redacted Stripe ID]; key [redacted key]"
                )
            },
        )

    @patch("accounts.views.stripe.PaymentMethod.retrieve")
    @patch("accounts.views.stripe.Webhook.construct_event")
    def test_successful_setup_webhook_saves_safe_card_details(
        self,
        construct_event,
        retrieve_payment_method,
    ):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.stripe_customer_id = "cus_test"
        profile.save(update_fields=["stripe_customer_id"])
        construct_event.return_value = {
            "type": "setup_intent.succeeded",
            "data": {
                "object": SimpleNamespace(
                    customer="cus_test",
                    payment_method="pm_test",
                )
            },
        }
        retrieve_payment_method.return_value = SimpleNamespace(
            id="pm_test",
            customer="cus_test",
            card=SimpleNamespace(brand="visa", last4="4242"),
        )

        with self.settings(STRIPE_WEBHOOK_SECRET="whsec_test"):
            response = self.client.post(
                reverse("stripe_webhook"),
                data=b"{}",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="test-signature",
            )

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.default_payment_method_id, "pm_test")
        self.assertEqual(profile.card_brand, "visa")
        self.assertEqual(profile.card_last4, "4242")
