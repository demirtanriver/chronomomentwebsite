from django.contrib.auth.backends import BaseBackend
# No need to import check_password if you're using organiser.check_password()
# from django.contrib.auth.hashers import check_password 
from .models import Organisers

class OrganiserBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            organiser = Organisers.objects.get(email=username) # 'username' here is the email from the form
        except Organisers.DoesNotExist:
            return None

        # IMPORTANT: Use the check_password method provided by AbstractBaseUser
        if organiser.check_password(password):
            return organiser
        else:
            return None

    def get_user(self, user_id):
        try:
            return Organisers.objects.get(pk=user_id)
        except Organisers.DoesNotExist:
            return None

