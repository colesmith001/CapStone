from django.shortcuts import render
from .forms import ContactForm

from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from .forms import ContactForm


# Create your views here.
def about_view(request):
  return render (request,'pages/about.html')

def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            message = form.cleaned_data["message"]

            email_message = EmailMessage(
                subject=f"New inquiry from {name}",
                body=f"Name: {name}\nEmail: {email}\n\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_RECIPIENT],
                reply_to=[email],
            )
            email_message.send()

            return redirect("contact")
    else:
        form = ContactForm()

    return render(request, "pages/contact.html", {"form": form})