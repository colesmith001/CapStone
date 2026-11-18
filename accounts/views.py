from django.views.decorators.csrf import csrf_exempt

import logging
import re
import stripe

from django.conf import settings
from django.http import JsonResponse


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import AccountInfoForm, ProfilePictureForm, SignupForm
from .models import UserProfile

from django.contrib.auth import login, logout

# Create your views here.
def signup_view(request):
    form = SignupForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("about")

    return render(request, "accounts/signup.html", {"form": form})

@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
  logout(request)
  return render(request, 'accounts/logout.html')


@login_required
def account_info_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    account_form = AccountInfoForm(instance=request.user)

    if request.method == "POST":
        field_name = request.POST.get("field")

        if field_name == "picture":
            picture_form = ProfilePictureForm(
                request.POST,
                request.FILES,
                instance=profile,
            )
            if picture_form.is_valid():
                picture_form.save()
                messages.success(request, "Your profile picture was updated.")
                return redirect("account_info")
        elif field_name in AccountInfoForm.Meta.fields:
            account_form = AccountInfoForm(request.POST, instance=request.user)
            account_form.fields = {
                field_name: account_form.fields[field_name],
            }
            if account_form.is_valid():
                account_form.save()
                messages.success(request, "Your account information was updated.")
                return redirect("account_info")
            picture_form = ProfilePictureForm(instance=profile)
        else:
            return HttpResponseBadRequest("Invalid account field.")
    else:
        picture_form = ProfilePictureForm(instance=profile)

    for field in account_form.fields.values():
        field.widget.attrs["readonly"] = True
        field.widget.attrs.setdefault("class", "form-control")
    picture_form.fields["picture"].widget.attrs["disabled"] = True
    picture_form.fields["picture"].widget.attrs.setdefault("class", "form-control")

    return render(
        request,
        "accounts/account_info.html",
        {"form": account_form, "picture_form": picture_form, "profile": profile},
    )

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def card_page(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    return render(
        request,
        "accounts/stripe.html",
        {
            "profile": profile,
            "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        },
    )

@login_required
@require_POST
def create_setup_intent(request):
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PUBLISHABLE_KEY:
        return JsonResponse(
            {"error": "Stripe card setup is unavailable because its API keys are not configured."},
            status=503,
        )

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    try:
        if not profile.stripe_customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                metadata={"user_id": str(request.user.pk)},
            )
            profile.stripe_customer_id = customer.id
            profile.save(update_fields=["stripe_customer_id"])

        intent = stripe.SetupIntent.create(
            customer=profile.stripe_customer_id,
            automatic_payment_methods={"enabled": True},
            usage="off_session",
        )
        return JsonResponse({"client_secret": intent.client_secret})
    except stripe.StripeError as exc:
        logger.exception("Could not start card setup for user %s", request.user.pk)
        if settings.DEBUG:
            error_details = [type(exc).__name__]
            error_code = getattr(exc, "code", None)
            error_param = getattr(exc, "param", None)
            user_message = getattr(exc, "user_message", None)
            if error_code:
                error_details.append(f"code={error_code}")
            if error_param:
                error_details.append(f"param={error_param}")
            if user_message:
                user_message = re.sub(
                    r"\b(?:sk|pk|rk)_(?:test|live)_[A-Za-z0-9]+\b",
                    "[redacted key]",
                    user_message,
                )
                user_message = re.sub(
                    r"\b(?:cus|pm|seti)_[A-Za-z0-9]+\b",
                    "[redacted Stripe ID]",
                    user_message,
                )
                error_details.append(user_message)
            return JsonResponse(
                {"error": f"Stripe request failed: {', '.join(error_details)}"},
                status=502,
            )
        return JsonResponse({"error": "could not start card setup"}, status=502)

@csrf_exempt #Stripe cannot send Django's browser CSRF token; the signature verifies Stripe.
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse("Stripe webhook is not configured.", status=503)

    payload = request.body
    signature = request.headers.get("Stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )

    except ValueError:
        return HttpResponseBadRequest("Invalid webhook payload")
    except stripe.SignatureVerificationError:
        return HttpResponseBadRequest("Invalid webhook signature")

    # Ignore other event types; this endpoint only needs to handle completed card setup.
    if event["type"] != "setup_intent.succeeded":
        return HttpResponse(status=200)

    setup_intent = event["data"]["object"]
    customer_id = getattr(setup_intent, "customer", None)
    payment_method_id = getattr(setup_intent, "payment_method", None)

    if not customer_id or not payment_method_id:
        return HttpResponseBadRequest("SetupIntent is missing card details")

    profile = UserProfile.objects.filter(
        stripe_customer_id=customer_id
    ).first()

    if profile is None:
        logger.error("No profile found for Stripe customer %s", customer_id)
        return HttpResponse("profile not found for stripe customer", status=500)

    try:
        payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
    except stripe.StripeError:
        logger.exception(
            "Could not retrieve Stripe PaymentMethod %s",
            payment_method_id,
        )
        return HttpResponse("Could not retrieve PaymentMethod.", status=502)

    if payment_method.customer != customer_id:
        return HttpResponseBadRequest("PaymentMethod does not belong to this customer.")

    card = payment_method.card
    if card is None:
        return HttpResponseBadRequest("PaymentMethod does not contain card details.")

    profile.default_payment_method_id = payment_method.id
    profile.card_brand = card.brand
    profile.card_last4 = card.last4
    profile.save(update_fields=[
        "default_payment_method_id",
        "card_brand",
        "card_last4",
    ])

    return HttpResponse(status=200)