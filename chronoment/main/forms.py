from django import forms

class CreateNewForm(forms.Form):
    first_name = forms.CharField(label="First Name",max_length=100)
    last_name =forms.CharField(label="Last Name",max_length=100)
    email =forms.CharField(label="Email",max_length=100)
    password_hash = forms.CharField(label="Password",max_length=100)
    address = forms.CharField(label="Address",max_length=100)
    phone_number = forms.CharField(label="Phone Number",max_length=100)




from .models import Stories # Assuming your models are in models.py in the same app

class StoryForm(forms.ModelForm):
    # The `qr_code_url` and timestamps (`created_at`, `updated_at`)
    # are typically not exposed directly in the form as they are
    # generated/managed by the system.
    # `organiser` is also set in the view, not by the user directly.
    class Meta:
        model = Stories
        fields = ['title', 'main_message', 'reveal_date'] # Fields the user fills out
        widgets = {
            'reveal_date': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'title': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'main_message': forms.Textarea(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
        }
        labels = {
            'title': 'Story Title',
            'main_message': 'Main Message of the Story',
            'reveal_date': 'Reveal Date',
        }
        help_texts = {
            'reveal_date': 'The date when the story becomes accessible to receivers.',
        }
