from django.views.decorators.csrf import csrf_exempt

import logging 
import stripe

from django.conf import settings
from django.http import JsonResponse


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import AccountInfoForm, ProfilePictureForm
from .models import UserProfile

from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm

# Create your views here.
def signup_view(request):
  form = UserCreationForm(
    request.POST if request.method == 'POST' else None
  )

  if request.method == 'POST' and form.is_valid():
    user = form.save()
    login(request, user)
    return redirect('about')

  return render(request, 'accounts/signup.html', {"form": form})


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
@require_POST
def create_setup_intent(request):
    if not settings.STRIPE_SECRET_KEY:
        return JsonResponse(
            {"error": "Stripe card setup is unavailable because STRIPE_SECRET_KEY is not configured."},
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
            payment_method_types=["card"],
            usage="off_session",
        )
    except stripe.StripeError:
        logger.exception("could not start card setyp for user %s", request.user.pk)
        return JsonResponse ({"error": "could not start card setup"}, status=502)
    return JsonResponse({"client_secret": intent.client_secret})

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
        return HttpResponseBadRequest("Inavlid webhook signature")

    # Ignore other event types; this endpoint only needs to handle completed card setup.
    if event["type"] != "setup_intent.succeeded":
        return HttpResponse(status=200)

    setup_intent = event["data"]["object"]
    customer_id = setup_intent.get("customer")
    payment_method_id = setup_intent.get("payment_method")

    if not customer_id or not payment_method_id:
        return H