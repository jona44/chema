
# customuser/middleware.py
from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.contrib import messages


class ProfileCompletionMiddleware:
    """
    Middleware to redirect users to appropriate pages based on profile completion status.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        exempt_url_names = [
            'login',
            'logout',
            'register',
            'profile',
            'profile_edit',
            'resend_verification',
            'verify_email',
        ]

        current_url_name = resolve(request.path_info).url_name

        is_exempt = (
            current_url_name in exempt_url_names or
            request.path.startswith('/admin/') or
            request.path.startswith('/static/') or
            request.path.startswith('/media/')
        )
        
        # Only apply logic to authenticated users on non-exempt URLs
        if (request.user.is_authenticated and 
            not is_exempt and 
            hasattr(request.user, 'profile')):
            
            profile = request.user.profile
            
            # If profile is incomplete, redirect to profile page
            if not profile.is_complete and current_url_name != 'profile':
                messages.info(
                    request, 
                    'Please complete your profile before continuing.'
                )
                return redirect('profile')
            
            # If profile is complete but user is on profile page, redirect to get_started
            elif (profile.is_complete and 
                current_url_name == 'profile' and 
                request.method == 'GET'):
                return redirect('get_started')

        response = self.get_response(request)
        return response
