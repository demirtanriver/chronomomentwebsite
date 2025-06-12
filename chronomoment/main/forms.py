from django import forms

class CreateNewForm(forms.Form):
    first_name = forms.CharField(label="First Name",max_length=100)
    last_name =forms.CharField(label="Last Name",max_length=100)
    email =forms.CharField(label="Email",max_length=100)
    password_hash = forms.CharField(label="Password",max_length=100)
    address = forms.CharField(label="Address",max_length=100)
    phone_number = forms.CharField(label="Phone Number",max_length=100)