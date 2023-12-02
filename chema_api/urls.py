# urls.py in your existing app

from django.urls import path
from .import views 

urlpatterns = [
    path('api/home/', views.home_api, name='home_api'),
    path('api/create_group/', views.create_group_api, name='create_group_api'),
    path('api/join_active_group/', views.join_active_group_api, name='join_active_group_api'),
    path('api/create_post/<int:group_id>/', views.create_post_api, name='create_post_api'),
    path('api/edit_post/<int:post_id>/', views.edit_post_api, name='edit_post_api'),
    path('api/delete_post/<int:post_id>/',views.delete_post_api, name='delete_post_api'),
    path('api/create_comment/<int:post_id>/', views.create_comment_api, name='create_comment_api'),
    path('api/edit_comment/<int:comment_id>/', views.edit_comment_api, name='edit_comment_api'),
    path('api/delete_comment/<int:comment_id>/', views.delete_comment_api, name='delete_comment_api'),
    path('api/add_member/<int:group_id>/', views.add_member_api, name='add_member_api'),
    path('api/add_dependent/', views.add_dependent_api, name='add_dependent_api'),
    path('api/add_reply/<int:comment_id>/', views.add_reply_api, name='add_reply_api'),
    path('api/remove_reply/<int:reply_id>/', views.remove_reply_api, name='remove_reply_api'),
    path('api/edit_reply/<int:reply_id>/', views.edit_reply_api, name='edit_reply_api'),
    path('api/search/', views.search_api, name='search_api'),
    path('api/member_detail/<int:group_id>/<int:member_id>/', views.member_detail_api, name='member_detail_api'),
    path('api/add_admin/<int:group_id>/', views.add_admin_api, name='add_admin_api'),
    path('api/toggle_group/<int:group_id>/', views.toggle_group_api, name='toggle_group_api'),
    
    # Add other API endpoints as needed
]
