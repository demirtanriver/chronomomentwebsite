from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Organisers)
admin.site.register(Stories)
admin.site.register(Senders)
admin.site.register(StorySenders)
admin.site.register(TextContribution)
admin.site.register(ImageContribution)
admin.site.register(VideoContribution)
