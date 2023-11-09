from .models import *

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