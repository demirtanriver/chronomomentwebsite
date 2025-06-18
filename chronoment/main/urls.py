from django.urls import path
from register import views as v
from . import views

urlpatterns = [
    path("",views.home, name="home"),
    path("<int:id>",views.index, name="index"),
    path("register/",v.register, name="register"),
]