from django import forms

class ContactForm(forms.Form):
  name = forms.CharField(
    max_length=50, widget=forms.TextInput(attrs={
      'class': 'form-control',
      'placeholder': 'Your name',
      'autocomplete': 'name'})
  )
  email = forms.EmailField(
    widget = forms.EmailInput(attrs={
      'class' : 'form-control',
      'placeholder' : 'you@example.com',
      'autocomplete': 'email'})
  )
  message = forms.CharField(
    widget=forms.Textarea(attrs = {
      'class': 'form-control',
      'placeholder': 'How can we help?',
      'rows': 5})
  )