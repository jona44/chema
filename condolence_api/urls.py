from django.urls import path
from .import views 

urlpatterns = [
     path('create_contribution_api/', views.create_contribution_api, name='create_contribution_api'),
     path('contribution_detail_api/<int:contribution_id>/', views.contribution_detail_api, name='contribution_detail_api'),
     path('deceased_api/', views.deceased_api, name='deceased_api'),
     path('toggle_deceased_api/<int:deceased_d>/', views.toggle_deceased_api, name='toggle_deceased_api'),
     path('stop_contributions_api/<int:deceased_d>/', views.stop_contributions_api, name='stop_contributions_api'),

]
