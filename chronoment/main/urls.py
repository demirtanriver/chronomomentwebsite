from django.urls import path
from register import views as v
from . import views
from django.conf import settings # Import settings
from django.conf.urls.static import static # Import static

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

    path('stories/<int:story_id>/manage-senders/', views.manage_senders_for_story, name='manage_senders_for_story'),
    
    path('story/join/<str:token>/', views.join_story_by_token, name='join_story_by_token'),
    
    # URL: Select Story for Adding Senders (sidebar link goes here)
    path('stories/select-for-senders/', views.select_story_for_senders, name='select_story_for_senders'),
]

# Serve media files during development (IMPORTANT: ONLY FOR DEVELOPMENT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
