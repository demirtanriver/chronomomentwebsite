from django.shortcuts import render
from django.http import HttpResponse
from .models import Stories
# Create your views here.

def index(response,id):
    st = Stories.objects.get(id=id)
    return HttpResponse("<h1>%s</h1>"%st.main_message)

