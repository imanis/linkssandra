from django import forms

class PostForm(forms.Form):
    body = forms.CharField(max_length=140)
