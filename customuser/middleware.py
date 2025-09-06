
# customuser/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class ProfileCompletionMiddleware:
    """
    Middleware to redirect users to appropriate pages based on profile completion status.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs that should be accessible regardless of profile completion
        exempt_urls = [
            reverse('login'),
            reverse('logout'),
            reverse('register'),
            reverse('profile'),
            reverse('profile_edit'),
            reverse('resend_verification'),
            '/admin/',  # Admin URLs
        ]
        
        # Add verification URLs (they contain parameters, so we check differently)
        current_path = request.path
        is_verification_url = '/verify-email/' in current_path
        
        # Check if current URL should be exempt
        is_exempt = (
            current_path in exempt_urls or 
            is_verification_url or 
            current_path.startswith('/admin/') or
            current_path.startswith('/static/') or
            current_path.startswith('/media/')
        )
        
        # Only apply logic to authenticated users on non-exempt URLs
        if (request.user.is_authenticated and 
            not is_exempt and 
            hasattr(request.user, 'profile')):
            
            profile = request.user.profile
            
            # If profile is incomplete, redirect to profile page
            if not profile.is_complete and current_path != reverse('profile'):
                messages.info(
                    request, 
                    'Please complete your profile before continuing.'
                )
                return redirect('profile')
            
            # If profile is complete but user is on profile page, redirect to get_started
            elif (profile.is_complete and 
                current_path == reverse('profile') and 
                request.method == 'GET'):
                return redirect('get_started')

        response = self.get_response(request)
        return response
