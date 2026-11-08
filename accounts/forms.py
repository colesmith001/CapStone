from django import forms
from .models import UserProfile
from django.contrib.auth import get_user_model

User = get_user_model()


class AccountInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["picture"]