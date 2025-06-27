from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from .models import Stories,Organisers
from .forms import CreateNewForm,OrganiserForm
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


