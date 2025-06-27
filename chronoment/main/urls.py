from django.urls import path
from register import views as v
from . import views

urlpatterns = [
    path("",views.home, name="home"),
    path("<int:id>",views.index, name="index"),
    path("register/",views.register, name="register"),
    path('login/', views.login, name='login'),
     # URL for creating a new story
    path('stories/create/', views.create_story, name='create_story'),

    # URL for viewing a specific story (needed for redirect after creation)
    # <int:story_id> captures an integer from the URL and passes it to the view.
    path('stories/<int:story_id>/', views.story_detail, name='story_detail'),
    path('logout/', views.user_logout, name='logout'),
]