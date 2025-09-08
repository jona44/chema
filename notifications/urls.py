from django.urls import path
from . import views

urlpatterns = [
    path('for-group/<slug:group_slug>/', views.group_notifications_view, name='group_notifications'),
]