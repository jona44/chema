# memorial/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Memorial pages
    path('<uuid:pk>/', views.memorial_detail_view, name='memorial_detail'),
    path('create/<slug:group_slug>/', views.create_memorial_view, name='create_memorial'),
    
    # Posts and content
    path('<uuid:pk>/posts/', views.memorial_posts_view, name='memorial_posts'),
    path('<uuid:memorial_pk>/post/create/', views.create_post_view, name='create_post'),
    path('post/<uuid:post_pk>/edit/', views.edit_post_view, name='edit_post'),
    path('post/<uuid:post_pk>/delete/', views.delete_post_view, name='delete_post'),
    
    # Condolences
    path('<uuid:memorial_pk>/condolences/', views.condolences_view, name='condolences'),
    
    # Funeral updates
    path('<uuid:memorial_pk>/updates/', views.funeral_updates_view, name='funeral_updates'),
    
    # Management
    path('<uuid:memorial_pk>/manage/', views.memorial_manage_view, name='memorial_manage'),
    
    # AJAX endpoints
    path('post/<uuid:post_pk>/like/', views.toggle_post_like, name='toggle_post_like'),
    path('post/<uuid:post_pk>/comment/', views.add_comment, name='add_comment'),
]