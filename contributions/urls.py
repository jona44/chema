from django.urls import path
from . import views

urlpatterns = [
    path('<slug:group_slug>/campaign/', views.campaign_detail_view, name='campaign_detail'),
]
