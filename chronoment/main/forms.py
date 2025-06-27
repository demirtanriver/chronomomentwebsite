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


from django import forms
from django.contrib.auth.hashers import make_password # For hashing passwords
from .models import Organisers # Import your Organisers model

from django import forms
from .models import Organisers # Import your Organisers model

class OrganiserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
        }),
        label="Password",
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
        }),
        label="Confirm Password"
    )

    class Meta:
        model = Organisers
        # Exclude password_hash (it's now 'password' field managed by AbstractBaseUser)
        fields = ['first_name', 'last_name', 'email', 'address', 'phone_number']
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': 'Your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': 'Your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': 'your.email@example.com'
            }),
            'address': forms.Textarea(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm resize-y',
                'rows': 3,
                'placeholder': 'Optional: Your street, city, postal code...'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': 'Optional: e.g., +447911123456'
            }),
        }
        
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
            'address': 'Address',
            'phone_number': 'Phone Number',
        }
        
        help_texts = {
            'email': 'We will use this email for account recovery and notifications.',
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match.")
        
        return cleaned_data

    # Save method now uses the custom manager's create_user method
    def save(self, commit=True):
        # We now use the custom manager to create the user
        # This handles hashing and setting required fields
        organiser = Organisers.objects.create_user(
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password'],
            address=self.cleaned_data.get('address'),
            phone_number=self.cleaned_data.get('phone_number')
            # Any other fields that are not automatically set
        )
        # If commit=False, you'd typically handle setting additional fields
        # and then saving the organiser manually. For simple creation,
        # create_user handles the save.
        return organiser
