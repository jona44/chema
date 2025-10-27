# groups/urls.py
from django.urls import path
from . import views
from . import manage_views

urlpatterns = [
    # Main pages
    
    path('browse/', views.browse_groups_view, name='browse_groups'),
    path('my-groups/', views.my_groups_view, name='my_groups'),
    
    # Group management
    path('create/', views.create_group_view, name='create_group'),
    path('<slug:slug>/join/', views.join_group_view, name='join_group'),
    path('<slug:slug>/leave/', views.leave_group_view, name='leave_group'),
    
    # Group administration
    path('dashboard/', manage_views.group_dashboard_view, name='group_dashboard'),
    path('<slug:slug>/manage/', manage_views.group_manage_view, name='group_manage'),
    path('<slug:slug>/manage/edit/', manage_views.group_edit_view, name='group_manage_edit'),
    path('<slug:slug>/manage/members/', manage_views.group_members_view, name='group_manage_members'),
    path('<slug:slug>/manage/invitations/', manage_views.group_invitations_view, name='group_manage_invitations'),
    path('<slug:slug>/manage/settings/', manage_views.group_settings_view, name='group_manage_settings'),
    
    # Member actions
    # Modal for managing a single member (HTMX)
    path('<slug:slug>/manage/member/<uuid:membership_id>/modal/', manage_views.group_manage_member_modal, name='group_manage_member_modal'),

    path('<slug:slug>/approve/<uuid:membership_id>/', views.approve_member_view, name='approve_member'),
    path('<slug:slug>/reject/<uuid:membership_id>/', views.reject_member_view, name='reject_member'),
    path('<slug:slug>/remove/<uuid:membership_id>/', views.remove_member_view, name='remove_member'),
    path('<slug:slug>/change-role/<uuid:membership_id>/', views.change_member_role_view, name='change_member_role'),
    # path('<slug:slug>/create-memorial/select-member/', manage_views.select_deceased_member_for_memorial_view, name='select_member_for_memorial'),
    
    # AJAX endpoints
    path('api/search-suggestions/', views.group_search_suggestions, name='group_search_suggestions'),
    path("groups/<slug:slug>/members/deceased/<int:pk>/",views.mark_deceased_view, name="mark-deceased"),
    
    
   


    
]