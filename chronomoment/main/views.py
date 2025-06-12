from django.shortcuts import render
from django.http import HttpResponse
from .models import Stories
# Create your views here.

def index(response,id):
    st = Stories.objects.get(id=id)
    return render(response, "main/story.html",{"st":st})

def home(response):
    return render(response, "main/home.html",{})

def story(response,id):
    st = Stories.objects.get(id=id)
    return render(response, "main/story.html",{"st":st})