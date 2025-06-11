from django.db import models

# Create your models here.
class Organisers(models.Model):
    first_name = models.CharField(max_length=200, null=False)
    last_name = models.CharField(max_length=200, null=False)
    email = models.EmailField(max_length=255, unique=True, null=False)
    password_hash = models.TextField(null=False) # Stores the hashed password

    # Optional Contact Information
    address = models.TextField(null=True, blank=True) # `blank=True` allows empty in forms
    phone_number = models.CharField(max_length=50, null=True, blank=True)

    # Timestamps for auditing
    created_at = models.DateTimeField(auto_now_add=True) # Automatically sets on creation
    updated_at = models.DateTimeField(auto_now=True) # Automatically updates on each save


    def __str__(self):
        return self.first_name + " " + self.last_name
    
    class Meta:
        verbose_name_plural = "Organisers" # Fixes pluralization in Django admin
    



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




class Media(models.Model):
    # Foreign Keys to link Media to Story and Sender
    story = models.ForeignKey(
        'Stories',
        on_delete=models.CASCADE, # If a story is deleted, its media is also deleted
        related_name='media_items' # Allows reverse access from Story object: story.media_items.all()
    )
    sender = models.ForeignKey(
        'Senders',
        on_delete=models.CASCADE, # If a sender is deleted, their uploaded media is also deleted
        related_name='uploaded_media' # Allows reverse access from Sender object: sender.uploaded_media.all()
    )

    # Media Content Information
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('text', 'Text Message'),
    ]
    media_type = models.CharField(
        max_length=20,
        choices=MEDIA_TYPE_CHOICES,
        null=False
    )
    s3_url = models.TextField(null=True, blank=True) # URL to the media file in S3 (for image/video)
    message_content = models.TextField(null=True, blank=True) # Actual text message content

    # Optional Description
    description = models.TextField(null=True, blank=True) # Caption/description for the media

    # Timestamps for auditing
    uploaded_at = models.DateTimeField(auto_now_add=True) # Renamed from created_at to be more specific

    # This method is used to define a human-readable representation of the object.
    def __str__(self):
        if self.media_type == 'text':
            return f"Text for '{self.story.title}' by {self.sender.name or self.sender.email}"
        return f"{self.media_type.capitalize()} for '{self.story.title}' by {self.sender.name or self.sender.email}"

    class Meta:
        verbose_name_plural = "Media" # Fixes pluralization in Django admin