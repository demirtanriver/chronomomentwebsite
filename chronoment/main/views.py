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
from datetime import datetime, time
import boto3 # <-- ADD THIS IMPORT
from botocore.exceptions import ClientError
# Create your views here.

def index(response,id):
    us = Organisers.objects.get(id=id)
    return render(response, "main/user.html",{"us":us})

def home(response):
    return render(response, "main/home.html",{})

def user(response,id):
    us = Organisers.objects.get(id=id)
    return render(response, "main/user.html",{"us":us})


def _check_and_update_story_sender_status(request, story_sender):
    """
    Checks if all contributions for a given StorySender are approved or ignored.
    If so, updates the StorySender's invitation_status to 'accepted'.
    """
    # Get all contributions associated with this StorySender
    all_text_contributions = TextContribution.objects.filter(story_sender=story_sender)
    all_image_contributions = ImageContribution.objects.filter(story_sender=story_sender)
    all_video_contributions = VideoContribution.objects.filter(story_sender=story_sender)

    # Combine all contributions into a single list
    all_contributions = list(all_text_contributions) + list(all_image_contributions) + list(all_video_contributions)

    # If there are no contributions, the status should not become 'accepted'
    # It should remain 'pending' if no contributions were ever made, or 'contributed' if some were made and then deleted.
    # We only update to 'accepted' if there are contributions AND all are reviewed.
    if not all_contributions:
        # If a sender had contributions that were all deleted, their status might need to revert from 'contributed'
        # to 'pending'. This is a more complex edge case, for now, we'll let it stay 'contributed' if it was.
        # If it's 'accepted' and all contributions are gone, it should revert.
        if story_sender.invitation_status == 'accepted':
            story_sender.invitation_status = 'contributed' # Or 'pending' depending on desired behavior for empty.
            story_sender.save()
            messages.info(request, f"All contributions from {story_sender.sender.name or story_sender.sender.email} for '{story_sender.story.title}' have been removed. Status reverted to 'Contributed'.")
        return


    # CHANGED: Check if ALL contributions have status 'approved' OR 'ignored'
    all_reviewed = all(c.status == 'approved' or c.status == 'ignored' for c in all_contributions)

    if all_reviewed and story_sender.invitation_status != 'accepted':
        story_sender.invitation_status = 'accepted'
        story_sender.save()
        messages.info(request, f"All contributions from {story_sender.sender.name or story_sender.sender.email} for '{story_sender.story.title}' have been reviewed (approved or ignored). Status updated to 'Accepted'.")
    elif not all_reviewed and story_sender.invitation_status == 'accepted':
        # This case handles if a previously reviewed contribution is changed back to 'pending',
        # or if a new 'pending' contribution is added after all others were reviewed.
        # Revert status back to 'contributed' if not all are reviewed anymore.
        story_sender.invitation_status = 'contributed'
        story_sender.save()
        messages.info(request, f"Not all contributions from {story_sender.sender.name or story_sender.sender.email} for '{story_sender.story.title}' have been reviewed. Status reverted to 'Contributed'.")


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
    
    existing_story_senders = StorySenders.objects.filter(story=story).order_by('sender__email')
    existing_senders_count = existing_story_senders.count()

    remaining_slots = max(0, story.max_senders - existing_senders_count)
    
    DynamicSenderFormSet = formset_factory(
        SenderForm, 
        extra=0,
        max_num=remaining_slots,
        validate_max=True
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_new_senders':
            formset = DynamicSenderFormSet(request.POST, prefix='senders')
            if formset.is_valid(): # This checks overall formset validity
                senders_added_count = 0
                for form in formset:
                    # IMPORTANT: Check individual form validity *before* accessing cleaned_data
                    if form.is_valid(): # Check if this specific form in the formset is valid
                        email = form.cleaned_data['email']
                        name = form.cleaned_data['name'] 

                        if existing_senders_count + senders_added_count >= story.max_senders:
                            messages.error(request, f"Cannot add more senders. Maximum limit of {story.max_senders} reached for this story.")
                            break 

                        sender, created = Senders.objects.get_or_create(
                            email=email,
                            defaults={'name': name} 
                        )
                        
                        if not created and sender.name != name:
                            sender.name = name
                            sender.save()
                            messages.info(request, f"Updated name for existing sender '{email}'.")

                        if StorySenders.objects.filter(story=story, sender=sender).exists():
                            messages.warning(request, f"Sender '{email}' is already invited to THIS story ('{story.title}').")
                            continue

                        invitation_token = uuid.uuid4().hex
                        token_expires_at = timezone.make_aware(timezone.datetime(
                            story.reveal_date.year, story.reveal_date.month, story.reveal_date.day, 23, 59, 59
                        ))

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
                            senders_added_count += 1
                        else:
                            messages.error(request, f"Failed to send invitation email to {email}.")
                    else:
                        # If an individual form is NOT valid, we should not proceed with it.
                        # The errors will be displayed by the template when it's re-rendered.
                        # We can add a message here if we want a general one, but specific field errors are better.
                        # For now, just continue to the next form or exit the loop if no valid forms.
                        messages.error(request, "One or more sender forms had validation errors. Please check the fields below.")
                        # This break is important: if the formset is not valid, we shouldn't try to process
                        # further forms, as it means the whole submission has issues.
                        break # Exit the loop if an invalid form is found
                
                if senders_added_count > 0:
                    messages.success(request, f"Successfully added and invited {senders_added_count} new sender(s).")
                else:
                    # Only show this if no senders were added and there were no other specific errors
                    if not formset.errors: # Check if the formset itself has no non-form errors
                        messages.info(request, "No new senders were added or all were duplicates for the current story.")
                
                return redirect(reverse('manage_senders_for_story', args=[story.id]))
            else:
                # If the overall formset is NOT valid, re-render the page with errors
                for form_idx, form in enumerate(formset):
                    if form.errors:
                        for field, errors in form.errors.items():
                            for error in errors:
                                messages.error(request, f"Error in Sender #{form_idx + 1} ({field}): {error}")
                messages.error(request, "Please correct the errors below to invite new senders.")
                context = {
                    'story': story,
                    'formset': formset, 
                    'existing_story_senders': existing_story_senders, 
                    'remaining_slots': remaining_slots, 
                    'page_title': f"Manage Senders for '{story.title}'"
                }
                return render(request, 'main/manage_senders_for_story.html', context)
        
        # ... (rest of the view for delete_sender, resend_invite, etc.)
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
            return redirect(request.META.get('HTTP_REFERER', reverse('home')))

        elif action == 'resend_invite':
            story_sender_id = request.POST.get('story_sender_id')
            if story_sender_id:
                try:
                    story_sender = get_object_or_404(StorySenders, id=story_sender_id, story=story)
                    
                    story_sender.invitation_token = uuid.uuid4().hex
                    token_expires_at = timezone.make_aware(timezone.datetime(
                        story.reveal_date.year, story.reveal_date.month, story.reveal_date.day, 23, 59, 59
                    ))
                    story_sender.invitation_status = 'pending' 
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
        'formset': formset, 
        'existing_story_senders': existing_story_senders, 
        'remaining_slots': remaining_slots, 
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

    if story_sender.token_expires_at and timezone.now() > story_sender.token_expires_at:
        messages.error(request, "This invitation link has expired.")
        story_sender.invitation_status = 'expired'
        story_sender.save()
        return render(request, 'main/join_story_by_token.html', {
            'page_title': 'Invitation Expired',
            'expired': True,
            'story_sender': story_sender,
            'story': story_sender.story,
            'sender': story_sender.sender,
        })

    story = story_sender.story
    sender = story_sender.sender

    text_form = TextContributionForm()
    image_form = ImageContributionForm()
    video_form = VideoContributionForm()

    if request.method == 'POST':
        contribution_type = request.POST.get('contribution_type')

        if contribution_type == 'text':
            text_form = TextContributionForm(request.POST)
            if text_form.is_valid():
                contribution = text_form.save(commit=False)
                contribution.story_sender = story_sender
                contribution.save()
                messages.success(request, "Your message has been added to the story!")
                story_sender.invitation_status = 'contributed'
                story_sender.save()
                return redirect(reverse('join_story_by_token', args=[token]))
            else:
                messages.error(request, "Please correct the errors in your message.")

        elif contribution_type == 'image':
            image_form = ImageContributionForm(request.POST, request.FILES)
            if image_form.is_valid():
                contribution = image_form.save(commit=False)
                contribution.story_sender = story_sender
                
                # --- DEBUGGING START: Image Upload ---
                print(f"DEBUG: Attempting to save image contribution for sender {story_sender.sender.email}")
                print(f"DEBUG: Image file received: {contribution.image.name if contribution.image else 'None'}")
                print(f"DEBUG: Image file size: {contribution.image.size if contribution.image else 'N/A'} bytes")
                try:
                    contribution.save() # This is where django-storages attempts to upload
                    print(f"DEBUG: Image contribution saved successfully. File path: {contribution.image.name}")
                    messages.success(request, "Your image has been added to the story!")
                    story_sender.invitation_status = 'contributed'
                    story_sender.save()
                    return redirect(reverse('join_story_by_token', args=[token]))
                except Exception as e:
                    print(f"ERROR: Exception during image upload: {e}")
                    import traceback
                    traceback.print_exc() # Print full traceback
                    messages.error(request, f"Failed to upload image: {e}")
                    # If upload fails, re-render the page with the form and error
                    context = {
                        'story_sender': story_sender,
                        'story': story,
                        'sender': sender,
                        'text_form': text_form,
                        'image_form': image_form, # Pass back the form with errors
                        'video_form': video_form,
                        'existing_text_contributions': TextContribution.objects.filter(story_sender=story_sender).order_by('-created_at'),
                        'existing_image_contributions': [], # No need to pre-sign if there's an error
                        'existing_video_contributions': [],
                        'page_title': f"Contribute to '{story.title}'"
                    }
                    return render(request, 'main/join_story_by_token.html', context)
                # --- DEBUGGING END: Image Upload ---
            else:
                messages.error(request, "Please correct the errors in your image upload.")

        elif contribution_type == 'video':
            video_form = VideoContributionForm(request.POST, request.FILES)
            if video_form.is_valid():
                contribution = video_form.save(commit=False) 
                contribution.story_sender = story_sender
                if 'youtube_video_id' in video_form.cleaned_data:
                    contribution.youtube_video_id = video_form.cleaned_data['youtube_video_id']
                
                # --- DEBUGGING START: Video Upload ---
                print(f"DEBUG: Attempting to save video contribution for sender {story_sender.sender.email}")
                print(f"DEBUG: Video file received: {contribution.video.name if contribution.video else 'None'}")
                print(f"DEBUG: Video file size: {contribution.video.size if contribution.video else 'N/A'} bytes")
                try:
                    contribution.save() # This is where django-storages attempts to upload
                    print(f"DEBUG: Video contribution saved successfully. File path: {contribution.video.name}")
                    messages.success(request, "Your video has been added to the story!")
                    story_sender.invitation_status = 'contributed'
                    story_sender.save()
                    return redirect(reverse('join_story_by_token', args=[token]))
                except Exception as e:
                    print(f"ERROR: Exception during video upload: {e}")
                    import traceback
                    traceback.print_exc() # Print full traceback
                    messages.error(request, f"Failed to upload video: {e}")
                    # If upload fails, re-render the page with the form and error
                    context = {
                        'story_sender': story_sender,
                        'story': story,
                        'sender': sender,
                        'text_form': text_form,
                        'image_form': image_form,
                        'video_form': video_form, # Pass back the form with errors
                        'existing_text_contributions': TextContribution.objects.filter(story_sender=story_sender).order_by('-created_at'),
                        'existing_image_contributions': [],
                        'existing_video_contributions': [], # No need to pre-sign if there's an error
                        'page_title': f"Contribute to '{story.title}'"
                    }
                    return render(request, 'your_app_name/join_story_by_token.html', context)
                # --- DEBUGGING END: Video Upload ---
            else:
                messages.error(request, "Please correct the errors in your video submission.")
        else:
            messages.error(request, "Invalid contribution type.")

    # ... (rest of join_story_by_token, including fetching existing contributions for GET request)
    # Fetch existing contributions for display by this specific sender to this story
    existing_text_contributions = TextContribution.objects.filter(story_sender=story_sender).order_by('-created_at')
    
    # --- UPDATED: Generate pre-signed URLs for images ---
    existing_image_contributions_with_urls = []
    for img_c in ImageContribution.objects.filter(story_sender=story_sender).order_by('-created_at'):
        if img_c.image: # Check if image file exists
            img_url = generate_presigned_url(img_c.image.name) # Use .name to get the S3 key
            if img_url:
                img_c.presigned_url = img_url # Add a new attribute to the object
        existing_image_contributions_with_urls.append(img_c)

    # --- UPDATED: Generate pre-signed URLs for videos ---
    existing_video_contributions_with_urls = []
    for vid_c in VideoContribution.objects.filter(story_sender=story_sender).order_by('-created_at'):
        if vid_c.video: # Check if video file exists
            vid_url = generate_presigned_url(vid_c.video.name) # Use .name to get the S3 key
            if vid_url:
                vid_c.presigned_url = vid_url # Add a new attribute to the object
        existing_video_contributions_with_urls.append(vid_c)

    context = {
        'story_sender': story_sender,
        'story': story,
        'sender': sender,
        'text_form': text_form,
        'image_form': image_form,
        'video_form': video_form,
        'existing_text_contributions': existing_text_contributions,
        'existing_image_contributions': existing_image_contributions_with_urls, # Pass the updated list
        'existing_video_contributions': existing_video_contributions_with_urls, # Pass the updated list
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

    # Convert story.reveal_date to a timezone-aware datetime at the start of that day
    reveal_datetime_start = timezone.make_aware(
        datetime.combine(story.reveal_date, time(0, 0, 0))
    )

    if reveal_datetime_start > timezone.now():
        messages.warning(request, "This story has not been revealed yet. Please check back on the reveal date.")
        if request.user.is_authenticated and request.user == story.organiser:
            return redirect(reverse('story_detail', args=[story.id]))
        return redirect(reverse('home'))

    # Fetch all APPROVED contributions for this story
    story_senders_for_story = StorySenders.objects.filter(story=story)

    processed_contributions = []

    # Fetch and prepare text contributions
    text_contributions = TextContribution.objects.filter(
        story_sender__in=story_senders_for_story,
        status='approved' 
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
    for text_c in text_contributions:
        processed_contributions.append(text_c)
    
    # Process Image Contributions - Generate pre-signed URLs here
    for img_c in ImageContribution.objects.filter(
        story_sender__in=story_senders_for_story,
        status='approved' 
    ).select_related('story_sender__sender'):
        presigned_img_url = None
        if img_c.image:
            presigned_img_url = generate_presigned_url(img_c.image.name) # <-- Generate pre-signed URL
        
        processed_contributions.append({
            'id': img_c.id,
            'type': 'image',
            'image_url': presigned_img_url, # <-- Use the pre-signed URL
            'caption': img_c.caption,
            'created_at': img_c.created_at,
            'contributor_name': img_c.story_sender.sender.name if img_c.story_sender.sender.name else img_c.story_sender.sender.email,
        })

    # Process Video Contributions - Generate pre-signed URLs here
    for vid_c in VideoContribution.objects.filter(
        story_sender__in=story_senders_for_story,
        status='approved' 
    ).select_related('story_sender__sender'):
        presigned_video_url = None
        if vid_c.video:
            presigned_video_url = generate_presigned_url(vid_c.video.name) # <-- Generate pre-signed URL
        
        processed_contributions.append({
            'id': vid_c.id,
            'type': 'video',
            'video_url': presigned_video_url, # <-- Use the pre-signed URL
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
    
    json_contributions = json.dumps(list(all_contributions_sorted), cls=DjangoJSONEncoder)

    context = {
        'story': story,
        'contributions': json_contributions, 
        'page_title': f"Story Slideshow: {story.title}"
    }
    return render(request, 'main/story_slideshow.html', context)


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
    story = get_object_or_404(Stories, id=story_id, organiser=request.user)
    story_sender = get_object_or_404(StorySenders, id=story_sender_id, story=story)

    text_contributions = TextContribution.objects.filter(
        story_sender=story_sender
    ).order_by('created_at')

    # --- UPDATED: Generate pre-signed URLs for images ---
    image_contributions_with_urls = []
    for img_c in ImageContribution.objects.filter(story_sender=story_sender).order_by('created_at'):
        if img_c.image:
            img_url = generate_presigned_url(img_c.image.name)
            if img_url:
                img_c.presigned_url = img_url
        image_contributions_with_urls.append(img_c)

    # --- UPDATED: Generate pre-signed URLs for videos ---
    video_contributions_with_urls = []
    for vid_c in VideoContribution.objects.filter(story_sender=story_sender).order_by('created_at'):
        if vid_c.video:
            vid_url = generate_presigned_url(vid_c.video.name)
            if vid_url:
                vid_c.presigned_url = vid_url
        video_contributions_with_urls.append(vid_c)

    context = {
        'story': story,
        'story_sender': story_sender,
        'sender_name': story_sender.sender.name if story_sender.sender.name else story_sender.sender.email,
        'text_contributions': text_contributions,
        'image_contributions': image_contributions_with_urls, # Pass the updated list
        'video_contributions': video_contributions_with_urls, # Pass the updated list
        'page_title': f"Contributions by {story_sender.sender.name or story_sender.sender.email} for '{story.title}'"
    }
    return render(request, 'main/sender_contributions.html', context)


# NEW: View to handle approval of a text contribution
@login_required
def approve_text_contribution(request, pk):
    if request.method == 'POST':
        contribution = get_object_or_404(TextContribution, pk=pk)
        if request.user == contribution.story_sender.story.organiser:
            # CHANGED: Set status to 'approved'
            contribution.status = 'approved'
            contribution.save()
            messages.success(request, "Text contribution approved successfully.")
            _check_and_update_story_sender_status(request, contribution.story_sender) 
        else:
            messages.error(request, "You are not authorized to approve this contribution.")
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))

# NEW: View to handle approval of an image contribution
@login_required
def approve_image_contribution(request, pk):
    if request.method == 'POST':
        contribution = get_object_or_404(ImageContribution, pk=pk)
        if request.user == contribution.story_sender.story.organiser:
            # CHANGED: Set status to 'approved'
            contribution.status = 'approved'
            contribution.save()
            messages.success(request, "Image contribution approved successfully.")
            _check_and_update_story_sender_status(request, contribution.story_sender)
        else:
            messages.error(request, "You are not authorized to approve this contribution.")
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))

# NEW: View to handle approval of a video contribution
@login_required
def approve_video_contribution(request, pk):
    if request.method == 'POST':
        contribution = get_object_or_404(VideoContribution, pk=pk)
        if request.user == contribution.story_sender.story.organiser:
            # CHANGED: Set status to 'approved'
            contribution.status = 'approved'
            contribution.save()
            messages.success(request, "Video contribution approved successfully.")
            _check_and_update_story_sender_status(request, contribution.story_sender)
        else:
            messages.error(request, "You are not authorized to approve this contribution.")
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))

# NEW: View to handle ignoring a text contribution
@login_required
def ignore_text_contribution(request, pk):
    if request.method == 'POST':
        contribution = get_object_or_404(TextContribution, pk=pk)
        if request.user == contribution.story_sender.story.organiser:
            # NEW: Set status to 'ignored'
            contribution.status = 'ignored'
            contribution.save()
            messages.info(request, "Text contribution marked as ignored.")
            _check_and_update_story_sender_status(request, contribution.story_sender) 
        else:
            messages.error(request, "You are not authorized to ignore this contribution.")
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))

# NEW: View to handle ignoring an image contribution
@login_required
def ignore_image_contribution(request, pk):
    if request.method == 'POST':
        contribution = get_object_or_404(ImageContribution, pk=pk)
        if request.user == contribution.story_sender.story.organiser:
            # NEW: Set status to 'ignored'
            contribution.status = 'ignored'
            contribution.save()
            messages.info(request, "Image contribution marked as ignored.")
            _check_and_update_story_sender_status(request, contribution.story_sender)
        else:
            messages.error(request, "You are not authorized to ignore this contribution.")
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))

# NEW: View to handle ignoring a video contribution
@login_required
def ignore_video_contribution(request, pk):
    if request.method == 'POST':
        contribution = get_object_or_404(VideoContribution, pk=pk)
        if request.user == contribution.story_sender.story.organiser:
            # NEW: Set status to 'ignored'
            contribution.status = 'ignored'
            contribution.save()
            messages.info(request, "Video contribution marked as ignored.")
            _check_and_update_story_sender_status(request, contribution.story_sender)
        else:
            messages.error(request, "You are not authorized to ignore this contribution.")
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
            _check_and_update_story_sender_status(request, story_sender)
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
            _check_and_update_story_sender_status(request, story_sender)
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
            _check_and_update_story_sender_status(request, story_sender)
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


def generate_presigned_url(file_path, expiration=3600): # Default expiration 1 hour (3600 seconds)
    """
    Generate a pre-signed URL to share an S3 object.
    :param file_path: The object's key (path) in the S3 bucket.
                      e.g., 'media/images/my_image.jpg'
    :param expiration: The time in seconds for the pre-signed URL to be valid.
    :return: The pre-signed URL as a string.
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': file_path},
            ExpiresIn=expiration
        )
    except ClientError as e:
        print(f"Error generating pre-signed URL: {e}")
        return None
    return response




