from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
import uuid # Assuming you use UUIDs for some models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin # Assuming for Organisers model

# Custom Manager for Organisers
class OrganiserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password) # set_password handles hashing
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) # Superusers should be active

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, first_name, last_name, password, **extra_fields)


# Your Organisers Model, now a Custom User Model
class Organisers(AbstractBaseUser, PermissionsMixin):
    # Personal Information
    first_name = models.CharField(max_length=200, null=False)
    last_name = models.CharField(max_length=200, null=False)
    email = models.EmailField(max_length=255, unique=True, null=False)
    
    # password_hash field is implicitly provided by AbstractBaseUser as 'password'
    # No need to define password_hash explicitly here. AbstractBaseUser handles it.

    # Optional Contact Information
    address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)

    # Required fields for AbstractBaseUser and PermissionsMixin
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) # Allows access to Django Admin
    date_joined = models.DateTimeField(default=timezone.now) # Required by AbstractBaseUser

    # Link to the custom manager
    objects = OrganiserManager()

    # Define the field used as the unique identifier for login
    USERNAME_FIELD = 'email'
    
    # Fields that will be prompted when creating a user via `createsuperuser`
    # (other than USERNAME_FIELD and password)
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name_plural = "Organisers" # Fixes pluralization in Django admin

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    # Methods required by PermissionsMixin
    # No need to define get_full_name or get_short_name if not directly used,
    # but good practice for custom user models.
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    



class Stories(models.Model):
    organiser = models.ForeignKey(Organisers, on_delete=models.CASCADE, related_name='stories')
    title = models.CharField(max_length=255)
    main_message = models.TextField()
    reveal_date = models.DateField()
    qr_code_url = models.URLField(max_length=500, blank=True, null=True) # URL for the QR code
    topper_identifier = models.CharField(
        max_length=100, 
        unique=True, 
        blank=False, 
        null=False,  
        help_text="Unique code printed on the physical cake topper's QR code."
    )
    # NEW FIELD: Max number of senders allowed for this story
    max_senders = models.PositiveIntegerField(
        default=6, # A reasonable default, adjust as needed
        help_text="Maximum number of senders allowed to contribute to this story."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Stories" # Correct pluralization for admin

    def __str__(self):
        return self.title




class Senders(models.Model):
    # Sender Information
    email = models.EmailField(max_length=255, unique=True, null=False)
    name = models.CharField(max_length=255, null=True, blank=True)

    # Timestamps for auditing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # This method is used to define a human-readable representation of the object.
    def __str__(self):
        return self.email

    class Meta:
        verbose_name_plural = "Senders" # Fixes pluralization in Django admin




class StorySenders(models.Model):
    # Foreign Keys to link Story and Sender
    story = models.ForeignKey(
        'Stories',
        on_delete=models.CASCADE, # If a story is deleted, this link is also deleted
        related_name='story_links' # Allows reverse access from Story object: story.story_links.all()
    )
    sender = models.ForeignKey(
        'Senders',
        on_delete=models.CASCADE, # If a sender is deleted, their links are also deleted
        related_name='story_links' # Allows reverse access from Sender object: sender.story_links.all()
    )

    # Story-specific sender data
    INVITATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('uploaded', 'Uploaded Media'),
        ('revoked', 'Revoked'),
    ]
    invitation_status = models.CharField(
        max_length=50,
        choices=INVITATION_STATUS_CHOICES,
        default='pending',
        null=False
    )
    invitation_token = models.CharField(max_length=255, unique=True, null=True, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    invited_at = models.DateTimeField(auto_now_add=True)
    last_reminded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Ensures that a sender can only be associated with a specific story once
        unique_together = ('story', 'sender')
        verbose_name_plural = "Story Senders" # Fixes pluralization in Django admin

    def __str__(self):
        return f"{self.story.title} - {self.sender.email} ({self.invitation_status})"




# Base Contribution Model (Abstract)
class BaseContribution(models.Model):
    story_sender = models.ForeignKey(StorySenders, on_delete=models.CASCADE)
    caption = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NEW: Status field for contributions
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('ignored', 'Ignored'), # Will not be shown in slideshow, but kept
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    class Meta:
        abstract = True
        ordering = ['created_at'] # Default ordering for all contributions



# --- ADD THIS SECTION ---
CONTRIBUTION_STATUS_CHOICES = [
    ('pending', 'Pending Review'),
    ('approved', 'Approved'),
    ('ignored', 'Ignored'),
]
# --- END ADD THIS SECTION ---

# Define your S3 storage instance
S3_MEDIA_STORAGE = S3Boto3Storage()

# ... (rest of your models.py, including Organisers, Stories, Senders, StorySenders, etc.)

class ImageContribution(models.Model):
    story_sender = models.ForeignKey(StorySenders, on_delete=models.CASCADE, related_name='image_contributions')
    image = models.ImageField(upload_to='contributions/images/', storage=S3_MEDIA_STORAGE)
    caption = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=10, choices=CONTRIBUTION_STATUS_CHOICES, default='pending') # Uses the defined choices
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Image by {self.story_sender.sender.email} for {self.story_sender.story.title}"

class VideoContribution(models.Model):
    story_sender = models.ForeignKey(StorySenders, on_delete=models.CASCADE, related_name='video_contributions')
    video = models.FileField(upload_to='contributions/videos/', blank=True, null=True, storage=S3_MEDIA_STORAGE)
    youtube_video_id = models.CharField(max_length=20, blank=True, null=True)
    caption = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=10, choices=CONTRIBUTION_STATUS_CHOICES, default='pending') # Uses the defined choices
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Video by {self.story_sender.sender.email} for {self.story_sender.story.title}"

# ... (and your TextContribution model, which also uses this)
class TextContribution(models.Model):
    story_sender = models.ForeignKey(StorySenders, on_delete=models.CASCADE, related_name='text_contributions')
    content = models.TextField()
    status = models.CharField(max_length=10, choices=CONTRIBUTION_STATUS_CHOICES, default='pending') # Uses the defined choices
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Text by {self.story_sender.sender.email} for {self.story_sender.story.title}"

