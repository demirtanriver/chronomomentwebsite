from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

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
    # Foreign Key to Organisers
    organiser = models.ForeignKey(
        'Organisers', # Refers to the Organisers model
        on_delete=models.CASCADE, # If an organiser is deleted, their stories are also deleted
        related_name='stories' # Allows reverse access from Organiser object: organiser.stories.all()
    )

    # Core Story Information
    title = models.CharField(max_length=255, null=False)
    main_message = models.TextField(null=False)
    qr_code_url = models.TextField(unique=True, null=False) # URL to the QR code image in S3
    reveal_date = models.DateField(null=False) # The date the story becomes accessible

    # Timestamps for auditing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # This method is used to define a human-readable representation of the object.
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Stories" # Fixes pluralization in Django admin




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




class TextContribution(models.Model):
    story_sender = models.ForeignKey(StorySenders, on_delete=models.CASCADE, related_name='text_contributions')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Text from {self.story_sender.sender.email} to {self.story_sender.story.title}"

# NEW: Image Contribution Model
class ImageContribution(models.Model):
    story_sender = models.ForeignKey(StorySenders, on_delete=models.CASCADE, related_name='image_contributions')
    # The 'upload_to' argument specifies a subdirectory within MEDIA_ROOT
    image = models.ImageField(upload_to='contributions/images/') 
    caption = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image from {self.story_sender.sender.email} to {self.story_sender.story.title}"


class VideoContribution(models.Model):
    story_sender = models.ForeignKey(StorySenders, on_delete=models.CASCADE, related_name='video_contributions')
    # Make video file optional
    video = models.FileField(upload_to='contributions/videos/', blank=True, null=True) 
    # New field for YouTube URL
    youtube_url = models.URLField(max_length=200, blank=True, null=True)
    # New field to store the extracted YouTube video ID for embedding
    youtube_video_id = models.CharField(max_length=50, blank=True, null=True) 
    caption = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.youtube_url:
            return f"YouTube Video from {self.story_sender.sender.email} to {self.story_sender.story.title}"
        elif self.video:
            return f"Uploaded Video from {self.story_sender.sender.email} to {self.story_sender.story.title}"
        return f"Video Contribution from {self.story_sender.sender.email} to {self.story_sender.story.title}"
