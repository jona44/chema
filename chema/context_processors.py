from .models import *
from django.shortcuts import  get_object_or_404

def user_groups(request):
    # Ensure the user is authenticated
    if request.user.is_authenticated:
        # Get the user's profile
        user_profile = Profile.objects.get(user=request.user)
        # Get the groups the user is a member of
        groups = Group.objects.filter(members=user_profile)
    else:
        groups = Group.objects.none()

    return {'groups': groups}

# def group_admins(request, group_id ):
#     group = get_object_or_404(Group,group_id=group_id)
#     group_admin = group.members.filter(groupmembership__is_admin=True)
    
#     return {'group_admin':group_admin}