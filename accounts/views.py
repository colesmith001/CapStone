from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

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