from django.urls import path
from . import views


app_name = 'memorial'

urlpatterns = [

    path('group/<slug:slug>/member/<uuid:membership_id>/create-memorial/',views.create_memorial_view, name='create_memorial'),  
    path('memorial/<uuid:pk>/', views.memorial_detail_view,name='memorial_detail'),
    path('memorial/<uuid:pk>/edit/',views.edit_memorial_view, name='edit_memorial'),
    path('memorial/<uuid:pk>/delete/', views.delete_memorial_view,name='delete_memorial'), 
    path('memorial/<uuid:pk>/admins/',  views.manage_family_admins_view,name='manage_family_admins'),
    path('group/<slug:slug>/memorials/',   views.group_memorials_list_view, name='group_memorials'), 

]