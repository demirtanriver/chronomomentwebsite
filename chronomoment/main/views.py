from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from .models import Stories,Organisers
from .forms import CreateNewForm
# Create your views here.

def index(response,id):
    us = Organisers.objects.get(id=id)
    return render(response, "main/user.html",{"us":us})

def home(response):
    return render(response, "main/home.html",{})

def user(response,id):
    us = Organisers.objects.get(id=id)
    return render(response, "main/user.html",{"us":us})

def create(response):
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
    return render(response, "main/create.html",{"form":form})