from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from .forms import CreateNewForm,OrganiserForm
from .forms import (
    OrganiserForm, StoryForm, SenderFormSet,
    TextContributionForm, ImageContributionForm, VideoContributionForm # NEW IMPORTS
)
# Import all models
from .models import (
    Organisers, Stories, Senders, StorySenders,
    TextContribution, ImageContribution, VideoContribution # NEW IMPORTS
)
# Create your views here.

def index(response,id):
    us = Organisers.objects.get(id=id)
    return render(response, "main/user.html",{"us":us})

def home(response):
    return render(response, "main/home.html",{})

def user(response,id):
    us = Organisers.objects.get(id=id)
    return render(response, "main/user.html",{"us":us})

def signup(response):
    if response.method == "POST":
        form = CreateNewForm(response.POST)

        if form.is_valid():
            f = form.cleaned_data["first_name"]
            l = form.cleaned_data["last_name"]
            e = form.cleaned_data["email"]
            p = form.cleaned_data["password_hash"] 
            a = form.cleaned_data["address"]
            pn = form.cleaned_data["phone_number"]
            o = Organisers(first_name = f,last_name=l, email=e,
                        password_hash=p, address=a, phone_number=pn )
            o.save()

        return HttpResponseRedirect("/%i" %o.id)
    else:
        form = CreateNewForm()
    return render(response, "main/signup.html",{"form":form})

def create(response):
    pass


def register(response):
    if response.method == "POST":
        form = OrganiserForm(response.POST)
        if form.is_valid():
            form.save()
    else:
        form = OrganiserForm()
    return render(response, "main/register.html", {"form":form})


from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login 
from django.contrib.auth.forms import AuthenticationForm

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login # Renamed login to avoid conflict
from django.contrib.auth.forms import AuthenticationForm # This form provides 'username' and 'password' fields


def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username') # AuthenticationForm's 'username' field is our 'email'
            password = form.cleaned_data.get('password')

            # The authenticate call will use your OrganiserBackend because it's listed first
            user = authenticate(request, username=email, password=password) 

            if user is not None:
                if user.is_active: # Check if the user account is active
                    auth_login(request, user)
                    messages.success(request, f"Welcome back, {user.first_name}!")
                    return redirect(reverse('home')) # Redirect to your home/dashboard page
                else:
                    messages.error(request, "Your account is inactive.")
            else:
                messages.error(request, "Invalid email or password.") # Generic message for security
        else:
            messages.error(request, "Please correct the errors below.")
            # The form.errors will be displayed by the template

    else: # GET request
        form = AuthenticationForm()

    context = {
        'form': form,
        'page_title': 'Login'
    }
    return render(request, 'main/login.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages # For displaying success/error messages
from django.contrib.auth.decorators import login_required # To ensure only logged-in users can create stories
import uuid # Used for generating a unique part of the QR code URL

# Make sure to import your StoryForm and Stories model
from .forms import StoryForm 
from .models import Stories, Organisers

@login_required # This decorator ensures that only authenticated users can access this view.
                # If a non-logged-in user tries to access it, they will be redirected to LOGIN_URL.
def create_story(request):
    """
    Handles the creation of a new Story by a logged-in Organiser.
    """
    # The request.user object will be an instance of your Organisers model
    # because you have set AUTH_USER_MODEL = 'your_app_name.Organisers' in settings.py.
    current_organiser = request.user 

    if request.method == 'POST':
        # If the request is POST, it means the form has been submitted.
        # Populate the form with the submitted data.
        form = StoryForm(request.POST) 
        if form.is_valid():
            # If the form data is valid:
            # 1. Create a Story instance but don't save it to the database yet (commit=False).
            #    This allows us to set the 'organiser' field before saving.
            story = form.save(commit=False)
            
            # 2. Assign the currently logged-in organiser to this story.
            story.organiser = current_organiser
            
            # 3. Generate a unique URL for the QR code.
            #    In a real application, this URL would point to an actual QR code image
            #    stored in AWS S3, or a dynamic endpoint that generates the QR code.
            #    For now, it's a placeholder.
            story.qr_code_url = f"https://yourdomain.com/story/qr/{uuid.uuid4()}/"
            
            # 4. Save the Story instance to the database.
            story.save()
            
            # 5. Display a success message to the user.
            messages.success(request, f"Story '{story.title}' created successfully! You can now invite senders.")
            
            # 6. Redirect the user to a new page, e.g., the story detail page.
            #    'story_detail' is the name of the URL pattern for viewing a single story.
            #    'args=[story.id]' passes the newly created story's ID to the URL.
            return redirect(reverse('story_detail', args=[story.id]))
        else:
            # If the form data is NOT valid:
            # Display an error message. The template will automatically show field-specific errors.
            messages.error(request, "Please correct the errors below to create your story.")
            # The form with errors will be passed to the template for re-rendering.
    else:
        # If the request is GET, it means the user is just visiting the page for the first time.
        # Create an empty form instance to display.
        form = StoryForm()

    # Prepare the context dictionary to pass data to the template.
    context = {
        'form': form,
        'page_title': 'Create New Story'
    }
    # Render the HTML template, passing the form and page title.
    return render(request, 'main/create_story.html', context)

# Placeholder for Story Detail View (you'll need to implement this fully later)
@login_required
def story_detail(request, story_id):
    # Retrieve the story, ensuring it belongs to the logged-in organiser
    story = get_object_or_404(Stories, id=story_id, organiser=request.user)
    context = {
        'story': story,
        'page_title': f"Story: {story.title}"
    }
    return render(request, 'main/story_detail.html', context)

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout # Ensure logout is imported
# User Logout View
@login_required # Ensures only logged-in users can initiate logout
def user_logout(request):
    """
    Logs out the current user, displays a message, and redirects to the login page.
    """
    auth_logout(request) # This is the Django built-in logout function
    messages.info(request, "You have been logged out.")
    return redirect(reverse('login')) # Redirect to the login page after logout


from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail # For sending emails
from django.conf import settings # To access settings like EMAIL_HOST_USER
from django.utils import timezone # For token expiration
import uuid # For generating unique tokens

from .forms import OrganiserForm, StoryForm, SenderFormSet # Import SenderFormSet
from .models import Organisers, Stories, Senders, StorySenders 

# Helper function to send invitation email (NEW)
def send_invitation_email(sender_email, sender_name, story_title, invitation_link):
    subject = f"You're invited to contribute to a Chronoment Story: '{story_title}'!"
    message = (
        f"Hi {sender_name or sender_email},\n\n"
        f"You've been invited to contribute to a Chronoment Story titled '{story_title}'.\n"
        f"To add your memories (photos, videos, or messages), please click on the link below:\n\n"
        f"{invitation_link}\n\n"
        f"This link is unique to you. Please do not share it.\n\n"
        f"We look forward to your contribution!\n"
        f"The Chronoment Team"
    )
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [sender_email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending email to {sender_email}: {e}")
        return False

@login_required
def manage_senders_for_story(request, story_id):
    story = get_object_or_404(Stories, id=story_id, organiser=request.user)
    
    # Fetch existing StorySenders for this story
    existing_story_senders = StorySenders.objects.filter(story=story).order_by('sender__email')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_new_senders':
            formset = SenderFormSet(request.POST, prefix='senders')
            if formset.is_valid():
                senders_added_count = 0
                for form in formset:
                    if form.cleaned_data: # Only process forms with data
                        email = form.cleaned_data['email']
                        name = form.cleaned_data.get('name', '')

                        sender, created = Senders.objects.get_or_create(
                            email=email,
                            defaults={'name': name}
                        )
                        if not created and name and sender.name != name:
                            sender.name = name
                            sender.save()

                        # Prevent duplicate invitations for the same story
                        if StorySenders.objects.filter(story=story, sender=sender).exists():
                            messages.warning(request, f"Sender '{email}' is already invited to this story.")
                            continue

                        invitation_token = uuid.uuid4().hex
                        token_expires_at = timezone.now() + timezone.timedelta(days=7) 

                        StorySenders.objects.create(
                            story=story,
                            sender=sender,
                            invitation_status='pending',
                            invitation_token=invitation_token,
                            token_expires_at=token_expires_at
                        )

                        invitation_link = request.build_absolute_uri(
                            reverse('join_story_by_token', args=[invitation_token])
                        )

                        if send_invitation_email(email, name, story.title, invitation_link):
                            messages.success(request, f"Invitation sent to {email}.")
                            senders_added_count += 1
                        else:
                            messages.error(request, f"Failed to send invitation email to {email}.")
                
                if senders_added_count > 0:
                    messages.success(request, f"Successfully added and invited {senders_added_count} new sender(s).")
                else:
                    messages.info(request, "No new senders were added or all were duplicates.")
                
                # Redirect to the same page to show updated list and clear form
                return redirect(reverse('manage_senders_for_story', args=[story.id]))
            else:
                messages.error(request, "Please correct errors in the new sender forms.")
        
        elif action == 'delete_sender':
            story_sender_id = request.POST.get('story_sender_id')
            if story_sender_id:
                try:
                    story_sender = get_object_or_404(StorySenders, id=story_sender_id, story=story)
                    email_to_delete = story_sender.sender.email
                    story_sender.delete()
                    messages.success(request, f"Sender '{email_to_delete}' has been removed from this story.")
                except Exception as e:
                    messages.error(request, f"Error removing sender: {e}")
            return redirect(reverse('manage_senders_for_story', args=[story.id]))

        elif action == 'resend_invite':
            story_sender_id = request.POST.get('story_sender_id')
            if story_sender_id:
                try:
                    story_sender = get_object_or_404(StorySenders, id=story_sender_id, story=story)
                    
                    # Generate new token and update expiration
                    story_sender.invitation_token = uuid.uuid4().hex
                    story_sender.token_expires_at = timezone.now() + timezone.timedelta(days=7)
                    story_sender.invitation_status = 'pending' # Reset status to pending if it was accepted/used
                    story_sender.save()

                    invitation_link = request.build_absolute_uri(
                        reverse('join_story_by_token', args=[story_sender.invitation_token])
                    )
                    
                    if send_invitation_email(story_sender.sender.email, story_sender.sender.name, story.title, invitation_link):
                        messages.success(request, f"Invitation resent to {story_sender.sender.email}.")
                    else:
                        messages.error(request, f"Failed to resend invitation to {story_sender.sender.email}.")
                except Exception as e:
                    messages.error(request, f"Error resending invitation: {e}")
            return redirect(reverse('manage_senders_for_story', args=[story.id]))
        
        # Add 'edit_sender' action if simple inline editing is desired later
        # elif action == 'edit_sender':
        #     story_sender_id = request.POST.get('story_sender_id')
        #     new_name = request.POST.get('new_name') # Or new_email, but email changes are complex
        #     if story_sender_id and new_name is not None:
        #         try:
        #             story_sender = get_object_or_404(StorySenders, id=story_sender_id, story=story)
        #             sender = story_sender.sender
        #             sender.name = new_name
        #             sender.save()
        #             messages.success(request, f"Sender name updated to '{new_name}'.")
        #         except Exception as e:
        #             messages.error(request, f"Error updating sender name: {e}")
        #     return redirect(reverse('manage_senders_for_story', args=[story.id]))


    else: # GET request
        formset = SenderFormSet(prefix='senders')

    context = {
        'story': story,
        'formset': formset, # For adding new senders
        'existing_story_senders': existing_story_senders, # For displaying existing senders
        'page_title': f"Manage Senders for '{story.title}'"
    }
    return render(request, 'main/manage_senders_for_story.html', context)


@login_required
def select_story_for_senders(request):
    """
    Displays a list of stories owned by the current organiser,
    allowing them to choose which story to add senders to.
    Only shows stories whose reveal_date is in the future.
    """
    # Fetch all stories belonging to the logged-in organiser
    # Filter for stories where the reveal_date is greater than today's date
    organiser_stories = Stories.objects.filter(
        organiser=request.user,
        reveal_date__gt=timezone.now().date() # Filter for future reveal dates
    ).order_by('-created_at') # Order by creation date, newest first

    context = {
        'stories': organiser_stories,
        'page_title': 'Select Story to Add Senders'
    }
    return render(request, 'main/select_story_for_senders.html', context)



def join_story_by_token(request, token):
    try:
        story_sender = get_object_or_404(StorySenders, invitation_token=token)
    except Exception:
        messages.error(request, "Invalid or missing invitation token.")
        return redirect(reverse('home'))

    # Check if the token has expired
    if story_sender.token_expires_at and timezone.now() > story_sender.token_expires_at:
        messages.error(request, "This invitation link has expired.")
        story_sender.invitation_status = 'expired'
        story_sender.save()
        # Render the template with an 'expired' flag to show appropriate message
        return render(request, 'your_app_name/join_story_by_token.html', {
            'page_title': 'Invitation Expired',
            'expired': True,
            'story_sender': story_sender,
            'story': story_sender.story,
            'sender': story_sender.sender,
        })

    story = story_sender.story
    sender = story_sender.sender

    # Initialize forms for GET request or if POST fails validation
    text_form = TextContributionForm()
    image_form = ImageContributionForm()
    video_form = VideoContributionForm() # Use the updated form

    if request.method == 'POST':
        contribution_type = request.POST.get('contribution_type')

        if contribution_type == 'text':
            text_form = TextContributionForm(request.POST)
            if text_form.is_valid():
                contribution = text_form.save(commit=False)
                contribution.story_sender = story_sender
                contribution.save()
                messages.success(request, "Your message has been added to the story!")
                story_sender.invitation_status = 'contributed' # Update status
                story_sender.save()
                return redirect(reverse('join_story_by_token', args=[token]))
            else:
                messages.error(request, "Please correct the errors in your message.")

        elif contribution_type == 'image':
            image_form = ImageContributionForm(request.POST, request.FILES)
            if image_form.is_valid():
                contribution = image_form.save(commit=False)
                contribution.story_sender = story_sender
                contribution.save()
                messages.success(request, "Your image has been added to the story!")
                story_sender.invitation_status = 'contributed' # Update status
                story_sender.save()
                return redirect(reverse('join_story_by_token', args=[token]))
            else:
                messages.error(request, "Please correct the errors in your image upload.")

        elif contribution_type == 'video':
            # Instantiate with request.POST for URL and caption, request.FILES for the file
            video_form = VideoContributionForm(request.POST, request.FILES)
            if video_form.is_valid():
                # The form's clean method has already set youtube_video_id and cleared 'video' if needed
                contribution = video_form.save(commit=False) 
                contribution.story_sender = story_sender
                
                # --- EXPLICIT ASSIGNMENT FIX ---
                # This line ensures the youtube_video_id from cleaned_data is explicitly set
                # on the model instance before saving.
                if 'youtube_video_id' in video_form.cleaned_data:
                    contribution.youtube_video_id = video_form.cleaned_data['youtube_video_id']
                # --- END EXPLICIT ASSIGNMENT FIX ---

                contribution.save() 
                messages.success(request, "Your video has been added to the story!")
                story_sender.invitation_status = 'contributed' # Update status
                story_sender.save()
                return redirect(reverse('join_story_by_token', args=[token]))
            else:
                messages.error(request, "Please correct the errors in your video submission.")
        else:
            messages.error(request, "Invalid contribution type.")

    # Fetch existing contributions for display by this specific sender to this story
    existing_text_contributions = TextContribution.objects.filter(story_sender=story_sender).order_by('-created_at')
    existing_image_contributions = ImageContribution.objects.filter(story_sender=story_sender).order_by('-created_at')
    existing_video_contributions = VideoContribution.objects.filter(story_sender=story_sender).order_by('-created_at')

    context = {
        'story_sender': story_sender,
        'story': story,
        'sender': sender,
        'text_form': text_form,
        'image_form': image_form,
        'video_form': video_form, # Pass the updated form
        'existing_text_contributions': existing_text_contributions,
        'existing_image_contributions': existing_image_contributions,
        'existing_video_contributions': existing_video_contributions,
        'page_title': f"Contribute to '{story.title}'"
    }
    return render(request, 'main/join_story_by_token.html', context)






