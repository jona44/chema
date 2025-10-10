from django.urls import path
from . import views
from . import memorial_feed_views
from . import poll_views

app_name = 'feeds'

urlpatterns = [
    path('<slug:slug>/', views.group_feed_view, name='group_feed'),
    path('<slug:group_slug>/create_post/', views.create_post_view, name='create_post'),
    path('posts/<uuid:post_id>/like/', views.toggle_post_like, name='toggle_post_like'),
    path('posts/<uuid:post_id>/comments/add/', views.create_comment, name='create_comment'),
    path('comments/<uuid:pk>/like/', views.toggle_comment_like, name='toggle_comment_like'),
    path('<slug:slug>/load_more/', views.load_more_posts, name='load_more_posts'),
    path('posts/<uuid:post_id>/comments/', views.load_comments, name='load_comments'),
    path('posts/<uuid:post_id>/delete/', views.delete_post, name='delete_post'),
    path('comments/<uuid:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('comments/<uuid:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comments/<uuid:comment_id>/edit-form/', views.get_edit_comment_form, name='get_edit_comment_form'),

    # Specific post type creation views
    path('<slug:group_slug>/posts/create/media/', views.create_media_post_view, name='create_media_post'),
    path('<slug:group_slug>/posts/create/announcement/', views.create_announcement_view, name='create_announcement'),
    path('<slug:group_slug>/posts/create/event/', views.create_event_post_view, name='create_event'),
    # path('<slug:group_slug>/posts/create/text/', views.create_text_post_view, name='create_text_post'),
    
    # # Modal rendering views
    path('<slug:group_slug>/modals/media-post/', views.get_media_post_modal, name='media_post_modal'),
    path('<slug:group_slug>/modals/announcement/', views.get_announcement_modal, name='announcement_modal'),
    path('<slug:group_slug>/modals/event/', views.get_event_modal, name='event_modal'),
    # path('<slug:group_slug>/modals/text-post/', views.get_text_post_modal, name='text_post_modal'),

    # Memorial-specific post creation views
    path('<slug:group_slug>/posts/create/memory/', memorial_feed_views.create_memory_post_view, name='create_memory_post'),
    path('<slug:group_slug>/posts/create/condolence/', memorial_feed_views.create_condolence_post_view, name='create_condolence_post'),
    path('<slug:group_slug>/posts/create/tribute/', memorial_feed_views.create_tribute_post_view, name='create_tribute_post'),
    path('<slug:group_slug>/posts/create/funeral-update/', memorial_feed_views.create_funeral_update_view, name='create_funeral_update'),
    path('<slug:group_slug>/modals/memory/', memorial_feed_views.get_memory_modal, name='memory_modal'),
    path('<slug:group_slug>/modals/condolence/', memorial_feed_views.get_condolence_modal, name='condolence_modal'),
    path('<slug:group_slug>/modals/tribute/', memorial_feed_views.get_tribute_modal, name='tribute_modal'),
    path('<slug:group_slug>/modals/funeral-update/', memorial_feed_views.get_funeral_update_modal, name='funeral_update_modal'),

    # Poll interaction
    path('posts/<uuid:post_id>/poll/vote/', poll_views.vote_poll_view, name='vote_poll'),
    path('posts/<uuid:post_id>/poll/remove-vote/', poll_views.remove_poll_vote_view, name='remove_poll_vote'),
    path('polls/<uuid:poll_id>/results/', poll_views.get_poll_results_view, name='poll_results'),
    path('polls/<uuid:poll_id>/voting/', poll_views.get_poll_voting_view, name='poll_voting'),


]