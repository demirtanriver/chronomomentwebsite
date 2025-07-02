from django import forms
from .models import Organisers, Stories, Senders, StorySenders, TextContribution, ImageContribution, VideoContribution # Import new models
import re

class CreateNewForm(forms.Form):
    first_name = forms.CharField(label="First Name",max_length=100)
    last_name =forms.CharField(label="Last Name",max_length=100)
    email =forms.CharField(label="Email",max_length=100)
    password_hash = forms.CharField(label="Password",max_length=100)
    address = forms.CharField(label="Address",max_length=100)
    phone_number = forms.CharField(label="Phone Number",max_length=100)





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



from django.contrib.auth.hashers import make_password # For hashing passwords


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
    

# You might have other forms here, like OrganiserForm, keep them.
from django.utils import timezone
# Story Creation Form
class StoryForm(forms.ModelForm):
    # Use DateInput with type="date" for native date picker
    reveal_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
        }),
        help_text="The date when the story will be revealed to receivers."
    )
    
    class Meta:
        model = Stories
        fields = ['title', 'main_message', 'reveal_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': 'e.g., Our Family Memories'
            }),
            'main_message': forms.Textarea(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm h-32',
                'placeholder': 'Write a heartfelt message that will be revealed with the story.'
            }),
        }

    # Custom validation for reveal_date
    def clean_reveal_date(self):
        reveal_date = self.cleaned_data['reveal_date']
        if reveal_date < timezone.now().date():
            raise forms.ValidationError("Reveal date cannot be in the past.")
        return reveal_date
from django.forms import formset_factory
# Form for a single Sender's details (NEW)
class SenderForm(forms.Form):
    email = forms.EmailField(
        label="Sender Email",
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'sender@example.com'
        }),
        help_text="Required. The email address of the person you want to invite."
    )
    name = forms.CharField(
        label="Sender Name (Optional)",
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Jane Doe'
        }),
        help_text="Optional. A name to identify this sender."
    )

# FormSet for multiple SenderForms (NEW)
# extra=1: Start with 1 empty form
# max_num=6: Allow a maximum of 6 forms
# validate_max=True: Enforce max_num validation
SenderFormSet = formset_factory(SenderForm, extra=1, max_num=6, validate_max=True)


# NEW: Form for Text Contributions
class TextContributionForm(forms.ModelForm):
    class Meta:
        model = TextContribution
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm h-32',
                'placeholder': 'Write your message here...'
            }),
        }
        labels = {
            'content': 'Your Message',
        }

# NEW: Form for Image Contributions
class ImageContributionForm(forms.ModelForm):
    class Meta:
        model = ImageContribution
        fields = ['image', 'caption']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-900 border border-gray-300 rounded-md cursor-pointer bg-gray-50 focus:outline-none focus:border-indigo-500'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': 'Add a caption (optional)'
            }),
        }
        labels = {
            'image': 'Upload Image',
            'caption': 'Image Caption',
        }

class VideoContributionForm(forms.ModelForm):
    class Meta:
        model = VideoContribution
        fields = ['video', 'youtube_url', 'caption'] # Include youtube_url field
        widgets = {
            'video': forms.ClearableFileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-900 border border-gray-300 rounded-md cursor-pointer bg-gray-50 focus:outline-none focus:border-indigo-500'
            }),
            'youtube_url': forms.URLInput(attrs={ # Use URLInput for proper validation and styling
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': 'e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': 'Add a caption (optional)'
            }),
        }
        labels = {
            'video': 'Upload Video File',
            'youtube_url': 'YouTube Video URL',
            'caption': 'Video Caption',
        }
        help_texts = {
            'video': 'Upload a video file (MP4, MOV, etc.).',
            'youtube_url': 'Or paste a YouTube video link. Only one video source (file or YouTube link) is allowed.',
        }

    def clean(self):
        cleaned_data = super().clean()
        video_file = cleaned_data.get('video')
        youtube_url = cleaned_data.get('youtube_url')
        
        # Ensure that the youtube_video_id is cleared by default if not set
        cleaned_data['youtube_video_id'] = None 

        print(f"DEBUG: VideoContributionForm clean method called.")
        print(f"DEBUG: video_file: {video_file}")
        print(f"DEBUG: youtube_url: {youtube_url}")

        if not video_file and not youtube_url:
            raise forms.ValidationError(
                "You must provide either a video file or a YouTube video URL."
            )
        
        if video_file and youtube_url:
            raise forms.ValidationError(
                "Please provide either a video file OR a YouTube video URL, but not both."
            )
        
        # If YouTube URL is provided, try to extract the video ID
        if youtube_url:
            youtube_id = self._extract_youtube_id(youtube_url)
            print(f"DEBUG: Extracted youtube_id from '{youtube_url}': {youtube_id}")
            if not youtube_id:
                raise forms.ValidationError("Invalid YouTube URL. Please check the link.")
            cleaned_data['youtube_video_id'] = youtube_id # Save extracted ID to cleaned_data
            cleaned_data['video'] = None # Ensure video file field is cleared if YouTube URL is used
        elif video_file:
            cleaned_data['youtube_url'] = None
            cleaned_data['youtube_video_id'] = None # Ensure this is explicitly cleared if file is used

        print(f"DEBUG: Final cleaned_data['youtube_video_id']: {cleaned_data.get('youtube_video_id')}")
        return cleaned_data

    def _extract_youtube_id(self, url):
        # This regex is designed to be highly robust for various YouTube URL formats.
        # It captures the 11-character video ID.
        youtube_regexes = [
            # Standard YouTube watch URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
            re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})(?:&.*)?'),
            # Shortened youtu.be URL: https://youtu.be/dQw4w9WgXcQ
            re.compile(r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})(?:\?si=[a-zA-Z0-9_-]+)?(?:&.*)?'),
            # Embed URL: https://www.youtube.com/embed/dQw4w9WgXcQ
            re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})(?:[?&].*)?'),
            # YouTube Music URL: https://music.youtube.com/watch?v=dQw4w9WgXcQ
            re.compile(r'(?:https?://)?(?:www\.)?music\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})(?:&.*)?'),
            # YouTube Shorts URL: https://www.youtube.com/shorts/([a-zA-Z0-9_-]{11})(?:[?&].*)?
            re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})(?:[?&].*)?'),
            # Old /v/ or /e/ URLs
            re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/(?:v|e)/([a-zA-Z0-9_-]{11})(?:[?&].*)?'),
        ]

        for regex in youtube_regexes:
            match = regex.match(url)
            if match:
                return match.group(1) # Group 1 always captures the video ID in these regexes
        return None

