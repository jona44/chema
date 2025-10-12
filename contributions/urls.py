# contributions/urls.py

from django.urls import path
from . import views

app_name = 'contributions'

urlpatterns = [
    # Campaign Management
    path('<slug:group_slug>/campaign/', views.campaign_detail_view, name='campaign_detail'),
    path('<slug:group_slug>/campaign/create/', views.create_campaign_view, name='create_campaign'),
    path('<slug:group_slug>/campaign/edit/', views.edit_campaign_view, name='edit_campaign'),
    
    # Making Contributions
    path('<slug:group_slug>/contribute/', views.make_contribution_view, name='make_contribution'),
    path('<slug:group_slug>/contribute/quick/', views.quick_contribute_view, name='quick_contribute'),
    path('<slug:group_slug>/contribution/<uuid:contribution_id>/success/', views.contribution_success_view, name='contribution_success'),
    
    # User's Contributions
    path('my-contributions/', views.my_contributions_view, name='my_contributions'),
    # Campaign Updates
    path('<slug:group_slug>/campaign/update/create/', views.create_update_view, name='create_update'),
    
    # Expense Tracking
    path('<slug:group_slug>/campaign/expense/record/', views.record_expense_view, name='record_expense'),
    
    # AJAX/HTMX
    path('<slug:group_slug>/campaign/stats/', views.campaign_stats_view, name='campaign_stats'),
    path('<slug:group_slug>/widget/', views.contribution_widget_view, name='contribution_widget'),
]