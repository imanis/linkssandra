from django import forms

class WelcomForm(forms.Form):
    firstname  = forms.RegexField(regex=r'^\w+$', max_length=30)
    lastname = forms.RegexField(regex=r'^\w+$', max_length=30)
    email = forms.EmailField(label=u"your e-mail")
   
    def clean(self):
        return self.cleaned_data

#    def save(self):
#        username = self.cleaned_data['firstname']
#        lastname = self.cleaned_data['lastname']
#        email = self.cleaned_data['email']
#        cass.save_user(username, password)
#        return username
