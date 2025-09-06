# customuser/utils.py
def get_redirect_url_for_user(user):
    """
    Helper function to determine where to redirect a user based on their profile status
    """
    if not user.is_authenticated:
        return 'login'
    
    if not hasattr(user, 'profile'):
        return 'profile'
    
    if user.profile.is_complete:
        return 'get_started'
    else:
        return 'profile'