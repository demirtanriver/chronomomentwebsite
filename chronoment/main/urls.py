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
    path('learn-more/', views.learn_more_page, name='learn_more'),
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
    path('stories/<int:story_id>/view/', views.view_revealed_story, name='view_revealed_story'),
    path('my-stories/', views.my_stories, name='my_stories'),

    path('story/view-public/<int:story_id>/', views.view_revealed_story, name='view_revealed_story_public'),
    path('topper/<str:topper_identifier>/', views.view_story_by_topper, name='view_story_by_topper'),

    path('stories/<int:story_id>/senders/<int:story_sender_id>/contributions/', views.view_sender_contributions, name='view_sender_contributions'),

    path('contributions/text/<int:pk>/approve/', views.approve_text_contribution, name='approve_text_contribution'),
    path('contributions/image/<int:pk>/approve/', views.approve_image_contribution, name='approve_image_contribution'),
    path('contributions/video/<int:pk>/approve/', views.approve_video_contribution, name='approve_video_contribution'),
    
    # NEW: URLs for deleting individual contributions (optional, but good for moderation)
    path('contributions/text/<int:pk>/delete/', views.delete_text_contribution, name='delete_text_contribution'),
    path('contributions/image/<int:pk>/delete/', views.delete_image_contribution, name='delete_image_contribution'),
    path('contributions/video/<int:pk>/delete/', views.delete_video_contribution, name='delete_video_contribution'),

    
]


# Serve media files during development (IMPORTANT: ONLY FOR DEVELOPMENT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
