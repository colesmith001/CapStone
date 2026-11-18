from django import forms
from .models import UserProfile
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class AccountInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["picture"]

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        autocomplete_values = {
            "username": "username",
            "email": "email",
            "password1": "new-password",
            "password2": "new-password",
        }
        for field_name, autocomplete in autocomplete_values.items():
            field = self.fields[field_name]
            field.widget.attrs.update({
                "class": "form-control",
                "autocomplete": autocomplete,
                "placeholder": field.label,
            })

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )
        return email