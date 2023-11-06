from django.urls import path
from . import views

urlpatterns = [
    path('create-contribution/', views.create_contribution, name='create_contribution'),
    path('contribution/<int:contribution_id>/', views.contribution_detail, name='contribution_detail'), 
    path('contributions_list/', views.contributions_list, name='contributions_list'),
]

