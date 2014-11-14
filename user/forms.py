from django import forms
from django.core.validators import validate_email

class WelcomForm(forms.Form):
    firstname  = forms.RegexField(regex=r'^\w+$', max_length=30)
    lastname = forms.RegexField(regex=r'^\w+$', max_length=30)
    email = forms.EmailField(label=u"your e-mail")
    photo = forms.ImageField(
        label='Select your profile picture',
		help_text='jpg, png'
    )

    def clean(self):
		return self.cleaned_data

