from django.urls import path
from .import views 

urlpatterns=[
    path('profile_api/', views.profile_api, name='profile_api'),
]