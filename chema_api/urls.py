# urls.py in your existing app

from django.urls import path
from .import views 

urlpatterns = [
    path('home_api/', views.home_api, name='home_api'),
    path('create_group_api/', views.create_group_api, name='create_group_api'),
    path('join_active_group_api/', views.join_active_group_api, name='join_active_group_api'),
    path('create_post/<int:group_id>/', views.create_post_api, name='create_post_api'),
    path('edit_post/<int:post_id>/', views.edit_post_api, name='edit_post_api'),
    path('delete_post/<int:post_id>/',views.delete_post_api, name='delete_post_api'),
    path('create_comment/<int:post_id>/', views.create_comment_api, name='create_comment_api'),
    path('edit_comment/<int:comment_id>/', views.edit_comment_api, name='edit_comment_api'),
    path('delete_comment/<int:comment_id>/', views.delete_comment_api, name='delete_comment_api'),
    path('add_member/<int:group_id>/', views.add_member_api, name='add_member_api'),
    path('add_dependent/', views.add_dependent_api, name='add_dependent_api'),
    path('add_reply/<int:comment_id>/', views.add_reply_api, name='add_reply_api'),
    path('remove_reply/<int:reply_id>/', views.remove_reply_api, name='remove_reply_api'),
    path('edit_reply/<int:reply_id>/', views.edit_reply_api, name='edit_reply_api'),
    path('search/', views.search_api, name='search_api'),
    path('member_detail/<int:group_id>/<int:member_id>/', views.member_detail_api, name='member_detail_api'),
    path('add_admin/<int:group_id>/', views.add_admin_api, name='add_admin_api'),
    path('toggle_group_api/<int:group_id>/', views.toggle_group_api, name='toggle_group_api'),
    
    # Add other API endpoints as needed
]
