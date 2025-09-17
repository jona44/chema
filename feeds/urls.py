# feeds/urls.py
from django.urls import path
from . import views

app_name = 'feeds'

urlpatterns = [
    # Main feed views
    path('<slug:slug>/feeds/', views.group_feed_view, name='group_feed'),
    path('group/<uuid:group_pk>/posts/', views.group_posts_view, name='group_posts'),
    
    # Post management
    path('group/<uuid:group_pk>/create-post/', views.create_post_view, name='create_post'),
    path('post/<uuid:pk>/', views.post_detail_view, name='post_detail'),
    path('post/<uuid:pk>/edit/', views.edit_post_view, name='edit_post'),
    path('post/<uuid:pk>/delete/', views.delete_post, name='delete_post'),
    
    # Post interactions (AJAX)
    path('api/post/<uuid:pk>/like/', views.toggle_post_like, name='toggle_post_like'),
    path('api/post/<uuid:pk>/comment/', views.add_comment, name='add_comment'),
    path('api/post/<uuid:pk>/share/', views.share_post, name='share_post'),
    
    # Poll interactions
    path('api/poll-option/<uuid:option_pk>/vote/', views.vote_poll, name='vote_poll'),
    
    # API endpoints
    path('api/group/<uuid:group_pk>/posts/', views.posts_api_view, name='posts_api'),
    
    # Memorial integration
    path('memorial/<uuid:memorial_pk>/feed/', views.memorial_feed_integration, name='memorial_feed'),
]