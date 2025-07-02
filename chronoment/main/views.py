from django.forms import formset_factory
from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from .forms import CreateNewForm,OrganiserForm
from .forms import (
    OrganiserForm, StoryForm, SenderForm,
    TextContributionForm, ImageContributionForm, VideoContributionForm # NEW IMPORTS
)
# Import all models
from .models import (
    Organisers, Stories, Senders, StorySenders,
    TextContribution, ImageContribution, VideoContribution # NEW IMPORTS
)
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages # For displaying success/error messages
from django.contrib.auth.decorators import login_required # To ensure only logged-in users can create stories
import uuid # Used for generating a unique part of the QR code URL

# Make sure to import your StoryForm and Stories model
from .forms import StoryForm 
from .models import Stories, Organisers

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
from itertools import chain
from django.db import models
import json # <--- NEW: Import json module
from django.core.serializers.json import DjangoJSONEncoder
# Create your views here.

def index(response,id):
    us = Organisers.objects.get(id=id)
    return render(response, "main/user.html",{"us":us})

def home(response):
    return render(response, "main/home.html",{})

def user(response,id):
    us = Organisers.objects.get(id=id)
    return render(response, "main/user.html",{"us":us})


def _check_and_update_story_sender_status(story_sender):
    """
    Checks if all contributions for a given StorySender are approved.
    If so, updates the StorySender's invitation_status to 'accepted'.
    """
    # Get all contributions associated with this StorySender
    all_text_contributions = TextContribution.objects.filter(story_sender=story_sender)
    all_image_contributions = ImageContribution.objects.filter(story_sender=story_sender)
    all_video_contributions = VideoContribution.objects.filter(story_sender=story_sender)

    # Combine all contributions into a single list (or just check counts)
    all_contributions = list(all_text_contributions) + list(all_image_contributions) + list(all_video_contributions)

    # If there are no contributions, the status should not become 'accepted'
    if not all_contributions:
        return

    # Check if ALL contributions are approved
    all_approved = all(c.is_approved for c in all_contributions)

    if all_approved and story_sender.invitation_status != 'accepted':
        story_sender.invitation_status = 'accepted'
        story_sender.save()
        messages.info(None, f"All contributions from {story_sender.sender.name or story_sender.sender.email} for '{story_sender.story.title}' have been approved. Status updated to 'Accepted'.")
    elif not all_approved and story_sender.invitation_status == 'accepted':
        # This case handles if a previously approved contribution is somehow unapproved
        # or if a new unapproved contribution is added after all others were approved.
        # Revert status back to 'contributed' if not all are approved anymore.
        story_sender.invitation_status = 'contributed'
        story_sender.save()
        messages.info(None, f"Not all contributions from {story_sender.sender.name or story_sender.sender.email} for '{story_sender.story.title}' are approved. Status reverted to 'Contributed'.")


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



@login_required
def create_story(request):
    current_organiser = request.user 

    if request.method == 'POST':
        form = StoryForm(request.POST)
        if form.is_valid():
            story = form.save(commit=False)
            story.organiser = current_organiser
            
            topper_identifier = form.cleaned_data.get('topper_identifier')
            if topper_identifier:
                story.qr_code_url = request.build_absolute_uri(
                    reverse('view_story_by_topper', args=[topper_identifier])
                )
            else:
                story.qr_code_url = None 

            # The max_senders field is now part of the form's cleaned_data
            # It will be saved automatically by form.save() because it's a model field.
            # No explicit line like story.max_senders = form.cleaned_data['max_senders'] is needed
            # as long as 'max_senders' is in StoryForm's Meta.fields.

            story.save() # Save the story instance, including max_senders
            messages.success(request, f"Story '{story.title}' created successfully!")
            return redirect(reverse('story_detail', args=[story.id]))
        else:
            messages.error(request, "Please correct the errors below to create your story.")
    else:
        form = StoryForm()

    context = {
        'form': form,
        'page_title': 'Create New Story'
    }
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
    existing_senders_count = existing_story_senders.count()

    # Calculate remaining slots
    remaining_slots = max(0, story.max_senders - existing_senders_count)
    
    # Determine how many extra forms to display initially
    # We want to show a few (e.g., 3) empty forms, but not more than remaining_slots
    initial_extra_forms = min(3, remaining_slots) 

    # Dynamically create the SenderFormSet
    DynamicSenderFormSet = formset_factory(
        SenderForm, 
        extra=initial_extra_forms, 
        max_num=remaining_slots, # Set max_num to the actual remaining slots
        validate_max=True
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_new_senders':
            formset = DynamicSenderFormSet(request.POST, prefix='senders')
            if formset.is_valid():
                senders_added_count = 0
                for form in formset:
                    if form.cleaned_data: # Only process forms with data
                        email = form.cleaned_data['email']
                        name = form.cleaned_data.get('name', '')

                        # Server-side check for max_senders limit before adding
                        if existing_senders_count + senders_added_count >= story.max_senders:
                            messages.error(request, f"Cannot add more senders. Maximum limit of {story.max_senders} reached for this story.")
                            # Break the loop and redirect, or continue to show errors for forms that would exceed limit
                            break # Exit loop if limit reached

                        sender, created = Senders.objects.get_or_create(
                            email=email,
                            defaults={'name': name} # Set name only if creating new sender
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


    else: # GET request
        formset = DynamicSenderFormSet(prefix='senders')

    context = {
        'story': story,
        'formset': formset, # For adding new senders
        'existing_story_senders': existing_story_senders, # For displaying existing senders
        'remaining_slots': remaining_slots, # Pass remaining slots to the template
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
        reveal_date__gte=timezone.now().date() # Filter for future reveal dates
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



def view_revealed_story(request, story_id):
    story = get_object_or_404(Stories, id=story_id) # No organiser check here yet, for future receiver access

    # Check if the story has been revealed
    if story.reveal_date > timezone.now().date():
        messages.warning(request, "This story has not been revealed yet. Please check back on the reveal date.")
        # If the user is an organiser, redirect them to their story detail page
        if request.user.is_authenticated and request.user == story.organiser:
            return redirect(reverse('story_detail', args=[story.id]))
        # Otherwise, redirect to home or a generic "not yet revealed" page
        return redirect(reverse('home')) # Or a specific 'not_revealed' page

    # If revealed, fetch all contributions related to this story
    story_senders_for_story = StorySenders.objects.filter(story=story)

    text_contributions = TextContribution.objects.filter(
        story_sender__in=story_senders_for_story
    ).order_by('created_at')

    image_contributions = ImageContribution.objects.filter(
        story_sender__in=story_senders_for_story
    ).order_by('created_at')

    video_contributions = VideoContribution.objects.filter(
        story_sender__in=story_senders_for_story
    ).order_by('created_at')
    
    context = {
        'story': story,
        'text_contributions': text_contributions,
        'image_contributions': image_contributions,
        'video_contributions': video_contributions,
        'page_title': f"Revealed Story: {story.title}"
    }
    return render(request, 'main/revealed_story.html', context)



@login_required
def story_detail(request, story_id):
    story = get_object_or_404(Stories, id=story_id, organiser=request.user)

    # Determine if the story has been revealed
    is_revealed = story.reveal_date <= timezone.now().date()

    context = {
        'story': story,
        'is_revealed': is_revealed, # Pass this flag to the template
        'page_title': f"Story: {story.title}"
    }
    return render(request, 'main/story_detail.html', context)



@login_required
def my_stories(request):
    # Fetch all stories created by the currently logged-in organiser
    # Order them by creation date, newest first
    organiser_stories = Stories.objects.filter(organiser=request.user).order_by('-created_at')

    context = {
        'stories': organiser_stories,
        'page_title': 'My Stories',
        'today': timezone.now().date(), # Pass today's date as a date object
    }
    return render(request, 'main/my_stories.html', context)


def view_story_by_topper(request, topper_identifier):
    try:
        story = Stories.objects.get(topper_identifier=topper_identifier)
    except Stories.DoesNotExist:
        messages.error(request, "No story found for this topper code.")
        return redirect(reverse('home'))

    if story.reveal_date > timezone.now().date():
        messages.warning(request, "This story has not been revealed yet. Please check back on the reveal date.")
        if request.user.is_authenticated and request.user == story.organiser:
            return redirect(reverse('story_detail', args=[story.id]))
        return redirect(reverse('home'))

    # Fetch all APPROVED contributions for this story
    story_senders_for_story = StorySenders.objects.filter(story=story)

    # Fetch and prepare text contributions
    text_contributions = TextContribution.objects.filter(
        story_sender__in=story_senders_for_story,
        is_approved=True
    ).annotate(
        contributor_name=models.Case(
            models.When(story_sender__sender__name__isnull=False, then=models.F('story_sender__sender__name')),
            default=models.F('story_sender__sender__email'),
            output_field=models.CharField()
        )
    ).values(
        'id', 'content', 'created_at', 'contributor_name'
    ).annotate(
        type=models.Value('text', output_field=models.CharField())
    )

    # Fetch and prepare image contributions - CRITICAL: Use .url for image field
    image_contributions = ImageContribution.objects.filter(
        story_sender__in=story_senders_for_story,
        is_approved=True
    ).annotate(
        contributor_name=models.Case(
            models.When(story_sender__sender__name__isnull=False, then=models.F('story_sender__sender__name')),
            default=models.F('story_sender__sender__email'),
            output_field=models.CharField()
        )
    ).values(
        'id', 'caption', 'created_at', 'contributor_name'
    ).annotate(
        # Manually add the image URL using F() expression if possible, or iterate later
        # For simplicity and direct JSON serialization, we'll get the object and process it.
        # This requires fetching full objects, not just values.
        type=models.Value('image', output_field=models.CharField())
    )

    # Fetch and prepare video contributions - CRITICAL: Use .url for video field
    video_contributions = VideoContribution.objects.filter(
        story_sender__in=story_senders_for_story,
        is_approved=True
    ).annotate(
        contributor_name=models.Case(
            models.When(story_sender__sender__name__isnull=False, then=models.F('story_sender__sender__name')),
            default=models.F('story_sender__sender__email'),
            output_field=models.CharField()
        )
    ).values(
        'id', 'youtube_url', 'youtube_video_id', 'caption', 'created_at', 'contributor_name'
    ).annotate(
        # Manually add the video URL using F() expression if possible, or iterate later
        # This also requires fetching full objects, not just values.
        type=models.Value('video', output_field=models.CharField())
    )

    # To get the .url for File/ImageFields, we need to fetch the full objects
    # and then manually convert them to dictionaries with the correct URLs.
    processed_contributions = []

    for text_c in text_contributions:
        processed_contributions.append(text_c)
    
    # Process Image Contributions
    for img_c in ImageContribution.objects.filter(
        story_sender__in=story_senders_for_story,
        is_approved=True
    ).select_related('story_sender__sender'): # Select related to avoid N+1 queries
        processed_contributions.append({
            'id': img_c.id,
            'type': 'image',
            'image': img_c.image.url if img_c.image else None, # Get the URL here
            'caption': img_c.caption,
            'created_at': img_c.created_at,
            'contributor_name': img_c.story_sender.sender.name if img_c.story_sender.sender.name else img_c.story_sender.sender.email,
        })

    # Process Video Contributions
    for vid_c in VideoContribution.objects.filter(
        story_sender__in=story_senders_for_story,
        is_approved=True
    ).select_related('story_sender__sender'): # Select related to avoid N+1 queries
        processed_contributions.append({
            'id': vid_c.id,
            'type': 'video',
            'video': vid_c.video.url if vid_c.video else None, # Get the URL here
            'youtube_url': vid_c.youtube_url,
            'youtube_video_id': vid_c.youtube_video_id,
            'caption': vid_c.caption,
            'created_at': vid_c.created_at,
            'contributor_name': vid_c.story_sender.sender.name if vid_c.story_sender.sender.name else vid_c.story_sender.sender.email,
        })

    # Combine all contributions and sort them by created_at
    all_contributions_sorted = sorted(
        processed_contributions,
        key=lambda x: x['created_at']
    )
    
    # Serialize the contributions list to JSON using Django's encoder
    json_contributions = json.dumps(list(all_contributions_sorted), cls=DjangoJSONEncoder)

    context = {
        'story': story,
        'contributions': json_contributions, # Pass the JSON string
        'page_title': f"Story Slideshow: {story.title}"
    }
    return render(request, 'main/story_slideshow.html', context) # Render new slideshow template

# Original view_revealed_story (now potentially redundant if view_story_by_topper is the primary public view)
# You can remove this or keep it if you foresee another use case for direct story_id access
# without a topper identifier. For now, view_story_by_topper covers the public viewing.
# If you keep it, ensure it's named differently than 'view_revealed_story_public' in urls.py
# and update any internal links that might still point to it.
# For simplicity, I'm assuming view_story_by_topper will be the only public access.
# If you need this specific view with story_id directly, we can re-add it with a different URL name.
# For now, I'm leaving it as is, but its URL name was removed from urls.py.
def view_revealed_story(request, story_id):
    story = get_object_or_404(Stories, id=story_id) # No organiser check here yet, for future receiver access

    # Check if the story has been revealed
    if story.reveal_date > timezone.now().date():
        messages.warning(request, "This story has not been revealed yet. Please check back on the reveal date.")
        # If the user is an organiser, redirect them to their story detail page
        if request.user.is_authenticated and request.user == story.organiser:
            return redirect(reverse('story_detail', args=[story.id]))
        # Otherwise, redirect to home or a generic "not yet revealed" page
        return redirect(reverse('home')) # Or a specific 'not_revealed' page

    # If revealed, fetch all contributions related to this story
    story_senders_for_story = StorySenders.objects.filter(story=story)

    text_contributions = TextContribution.objects.filter(
        story_sender__in=story_senders_for_story
    ).order_by('created_at') # Order by creation date for chronological display

    image_contributions = ImageContribution.objects.filter(
        story_sender__in=story_senders_for_story
    ).order_by('created_at')

    video_contributions = VideoContribution.objects.filter(
        story_sender__in=story_senders_for_story
    ).order_by('created_at')
    
    context = {
        'story': story,
        'text_contributions': text_contributions,
        'image_contributions': image_contributions,
        'video_contributions': video_contributions,
        'page_title': f"Revealed Story: {story.title}"
    }
    return render(request, 'main/revealed_story.html', context)


@login_required
def view_sender_contributions(request, story_id, story_sender_id):
    # Ensure the story belongs to the current organiser
    story = get_object_or_404(Stories, id=story_id, organiser=request.user)
    
    # Ensure the story_sender is linked to this story
    story_sender = get_object_or_404(StorySenders, id=story_sender_id, story=story)

    # Fetch all contributions for this specific StorySender
    text_contributions = TextContribution.objects.filter(
        story_sender=story_sender
    ).order_by('created_at')

    image_contributions = ImageContribution.objects.filter(
        story_sender=story_sender
    ).order_by('created_at')

    video_contributions = VideoContribution.objects.filter(
        story_sender=story_sender
    ).order_by('created_at')

    context = {
        'story': story,
        'story_sender': story_sender,
        'sender_name': story_sender.sender.name if story_sender.sender.name else story_sender.sender.email,
        'text_contributions': text_contributions,
        'image_contributions': image_contributions,
        'video_contributions': video_contributions,
        'page_title': f"Contributions by {story_sender.sender.name or story_sender.sender.email} for '{story.title}'"
    }
    return render(request, 'main/sender_contributions.html', context)


# NEW: View to handle approval of a text contribution
@login_required
def approve_text_contribution(request, pk):
    if request.method == 'POST':
        contribution = get_object_or_404(TextContribution, pk=pk)
        if request.user == contribution.story_sender.story.organiser:
            contribution.is_approved = True
            contribution.save()
            messages.success(request, "Text contribution approved successfully.")
            _check_and_update_story_sender_status(contribution.story_sender) # Call helper
        else:
            messages.error(request, "You are not authorized to approve this contribution.")
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))

# NEW: View to handle approval of an image contribution
@login_required
def approve_image_contribution(request, pk):
    if request.method == 'POST':
        contribution = get_object_or_404(ImageContribution, pk=pk)
        if request.user == contribution.story_sender.story.organiser:
            contribution.is_approved = True
            contribution.save()
            messages.success(request, "Image contribution approved successfully.")
            _check_and_update_story_sender_status(contribution.story_sender) # Call helper
        else:
            messages.error(request, "You are not authorized to approve this contribution.")
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))

# NEW: View to handle approval of a video contribution
@login_required
def approve_video_contribution(request, pk):
    if request.method == 'POST':
        contribution = get_object_or_404(VideoContribution, pk=pk)
        if request.user == contribution.story_sender.story.organiser:
            contribution.is_approved = True
            contribution.save()
            messages.success(request, "Video contribution approved successfully.")
            _check_and_update_story_sender_status(contribution.story_sender) # Call helper
        else:
            messages.error(request, "You are not authorized to approve this contribution.")
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))

# NEW: View to handle deletion of a text contribution
@login_required
def delete_text_contribution(request, pk):
    if request.method == 'POST':
        contribution = get_object_or_404(TextContribution, pk=pk)
        story_sender = contribution.story_sender # Get story_sender before deleting contribution
        if request.user == story_sender.story.organiser:
            contribution.delete()
            messages.success(request, "Text contribution deleted successfully.")
            _check_and_update_story_sender_status(story_sender) # Call helper after deletion
        else:
            messages.error(request, "You are not authorized to delete this contribution.")
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))

# NEW: View to handle deletion of an image contribution
@login_required
def delete_image_contribution(request, pk):
    if request.method == 'POST':
        contribution = get_object_or_404(ImageContribution, pk=pk)
        story_sender = contribution.story_sender # Get story_sender before deleting contribution
        if request.user == story_sender.story.organiser:
            contribution.delete()
            messages.success(request, "Image contribution deleted successfully.")
            _check_and_update_story_sender_status(story_sender) # Call helper after deletion
        else:
            messages.error(request, "You are not authorized to delete this contribution.")
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))

# NEW: View to handle deletion of a video contribution
@login_required
def delete_video_contribution(request, pk):
    if request.method == 'POST':
        contribution = get_object_or_404(VideoContribution, pk=pk)
        story_sender = contribution.story_sender # Get story_sender before deleting contribution
        if request.user == story_sender.story.organiser:
            contribution.delete()
            messages.success(request, "Video contribution deleted successfully.")
            _check_and_update_story_sender_status(story_sender) # Call helper after deletion
        else:
            messages.error(request, "You are not authorized to delete this contribution.")
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))


def learn_more_page(request):
    """
    Renders the 'Learn More' page, providing information for Senders & Receivers.
    """
    context = {
        'page_title': 'Learn More about Chronoment'
    }
    return render(request, 'main/learn_more.html', context)




