from django.urls import path
from register import views as v
from . import views
from django.conf import settings # Import settings
from django.conf.urls.static import static # Import static

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('create-story/', views.create_story, name='create_story'),
    path('story/<int:story_id>/', views.story_detail, name='story_detail'),
    path('my-stories/', views.my_stories, name='my_stories'),
    path('select-story-for-senders/', views.select_story_for_senders, name='select_story_for_senders'),
    path('story/<int:story_id>/manage-senders/', views.manage_senders_for_story, name='manage_senders_for_story'),
    path('join/<str:token>/', views.join_story_by_token, name='join_story_by_token'),
    path('topper/<str:topper_identifier>/', views.view_story_by_topper, name='view_story_by_topper'),
    path('revealed-story/<int:story_id>/', views.view_revealed_story, name='view_revealed_story'), # This is currently redundant
    path('story/<int:story_id>/sender/<int:story_sender_id>/contributions/', views.view_sender_contributions, name='view_sender_contributions'),
    path('contributions/text/<int:pk>/approve/', views.approve_text_contribution, name='approve_text_contribution'),
    path('contributions/image/<int:pk>/approve/', views.approve_image_contribution, name='approve_image_contribution'),
    path('contributions/video/<int:pk>/approve/', views.approve_video_contribution, name='approve_video_contribution'),
    path('contributions/text/<int:pk>/ignore/', views.ignore_text_contribution, name='ignore_text_contribution'),
    path('contributions/image/<int:pk>/ignore/', views.ignore_image_contribution, name='ignore_image_contribution'),
    path('contributions/video/<int:pk>/ignore/', views.ignore_video_contribution, name='ignore_video_contribution'),
    path('contributions/text/<int:pk>/delete/', views.delete_text_contribution, name='delete_text_contribution'),
    path('contributions/image/<int:pk>/delete/', views.delete_image_contribution, name='delete_image_contribution'),
    path('contributions/video/<int:pk>/delete/', views.delete_video_contribution, name='delete_video_contribution'),

    path('learn-more/', views.learn_more_page, name='learn_more'),
]


# Serve media files during development (IMPORTANT: ONLY FOR DEVELOPMENT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
