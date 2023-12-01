# urls.py in your existing app

from django.urls import path
from .import views 

urlpatterns = [
    path('api/create_group/', views.create_group_api, name='create_group_api'),
    path('api/join_active_group/', views.join_active_group_api, name='join_active_group_api'),
    
    # Add other API endpoints as needed
]
