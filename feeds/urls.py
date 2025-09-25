from django.urls import path
from . import views

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
]