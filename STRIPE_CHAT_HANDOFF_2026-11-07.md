# Stripe chat handoff — 2026-11-07

This note captures today's discussion so a future session can continue the Stripe card-saving work.

## What we discussed

The project is a Django app with user profiles and a product cart. The user asked how to add Stripe so users can save a card to their account for future payments, then asked for more detail about:

1. **Step 3: Stripe.js card collection.** The browser requests a SetupIntent client secret from Django, mounts Stripe's Payment Element, and uses `stripe.confirmSetup()`. Card number and CVC go directly to Stripe, not to Django. The publishable key is okay in browser code; the secret key must remain server-side.
2. **Step 4: Stripe webhook.** Stripe sends a server-to-server `setup_intent.succeeded` event after setup succeeds. Django verifies the event's Stripe signature, uses the SetupIntent's Customer ID to find the profile, retrieves the PaymentMethod, and stores its Stripe ID plus safe display details such as brand and last four digits. Do not trust browser-submitted payment status or store card number/CVC.

For future off-session payments, the SetupIntent should use `usage="off_session"`. A later payment can still require customer authentication or fail, so the app should handle Stripe errors and ask the customer to complete payment when needed.

## Code and configuration discussed

- Add a Stripe Customer ID, default PaymentMethod ID, card brand, and last-four fields to the profile model.
- Configure `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, and `STRIPE_WEBHOOK_SECRET` from environment variables.
- A login-protected `create_setup_intent` Django view creates/reuses a Stripe Customer and returns the SetupIntent's `client_secret`.
- The save-card page uses Stripe.js Payment Element and posts to the setup endpoint with Django's CSRF token.
- Add a separate webhook URL, e.g. `/accounts/stripe/webhook/`, for Stripe to deliver events. This is different from the endpoint the browser calls to create a SetupIntent.
- For local webhook testing, use Stripe CLI forwarding, e.g.:

  ```powershell
  stripe listen --forward-to localhost:8000/accounts/stripe/webhook/
  ```

  Use the signing secret printed by Stripe CLI as the local `STRIPE_WEBHOOK_SECRET`.

- Use Stripe test mode and test card `4242 4242 4242 4242` for test transactions only.

## Items to verify in the current code

These were observed in the files during today's discussion; check that they are still accurate before making changes:

- `templates/accounts/stripe.html` fetches `{% url 'create_setup_intent' %}`, but the reviewed `accounts/urls.py` registered the view as `name="card_info"`. Make the URL name and template reference agree.
- The reviewed `accounts/models.py` had a misspelled field `defualt_payment_method_id`; the webhook example expects `default_payment_method_id`. Correct the spelling and create/apply a migration if it has not already been done.
- The reviewed `accounts/models.py` also had duplicate declarations of `user` and `picture`; inspect before editing.
- `config/settings.py` reads the three Stripe variables directly from the environment, so all must be set or Django settings import will fail.
- The webhook example is not yet confirmation that a webhook has been implemented. Verify the current `accounts/views.py` and URL configuration.

## Suggested next steps

1. Inspect the current model, account URLs, Stripe page, settings, and views; the files may have changed since they were reviewed.
2. Fix any model field typo/duplicates and URL-name mismatch, then run account migrations.
3. Implement and register a signature-verified `setup_intent.succeeded` webhook.
4. Configure Stripe CLI or a Stripe Dashboard endpoint and test a successful setup event.
5. Show the saved brand and last four digits on the signed-in user's account page.
6. Add a separate checkout/order flow if the goal includes charging for cart purchases; calculate the total server-side and only mark an order paid after a verified Stripe payment event.


explain to me what else I need to implement stripe api to simulate card info onto users accounts with code examples // prompt to get back to AI help 