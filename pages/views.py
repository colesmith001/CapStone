from django.shortcuts import render
from .forms import ContactForm

# Create your views here.
def about_view(request):
  return render (request,'pages/about.html')

def contact_view(request):
  if request.method == "POST":
    form = ContactForm(request.POST)
    if form.is_valid():
      # Handle the valid form data here.
      # For example: send an email or save a message.
      pass
  else:
    form = ContactForm()

  return render(request, "pages/contact.html", {"form": form})
