# customuser/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils import timezone

from .models import CustomUser, Profile
from .forms import CustomUserCreationForm, CustomUserLoginForm, ProfileUpdateForm


@csrf_protect
def register_view(request):
    """User registration with email verification"""
    if request.user.is_authenticated:
        return redirect('profile')  # or wherever you want logged-in users to go
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Create inactive user
            user = form.save(commit=False)
            user.is_active = False
            user.is_email_verified = False
            user.save()
            
            # Send verification email
            send_verification_email(request, user)
            
            messages.success(
                request, 
                f'Account created successfully! Please check your email ({user.email}) to verify your account.'
            )
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'customuser/register.html', {'form': form})


def send_verification_email(request, user):
    """Send email verification link"""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    verification_link = request.build_absolute_uri(
        reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    )
    
    subject = 'Verify Your Email Address'
    message = render_to_string('customuser/emails/verification_email.html', {
        'user': user,
        'verification_link': verification_link,
        'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Our Site',
    })
    
    send_mail(
        subject,
        '',  # Plain text version (optional)
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=message,
        fail_silently=False,
    )


def verify_email_view(request, uidb64, token):
    """Email verification view"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.is_active = True  # Activate user after email verification
        user.save()
        
        messages.success(request, 'Your email has been verified successfully! You can now log in.')
        return redirect('login')
    else:
        messages.error(request, 'Email verification link is invalid or has expired.')
        return redirect('register')


@csrf_protect
@never_cache
def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        # Redirect authenticated users with a profile straight to my-groups
        if getattr(request.user, "profile", None):
            return redirect("my_groups")
        return redirect("my_groups")

    if request.method == "POST":
        form = CustomUserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")

            user = authenticate(request, username=email, password=password)
            if user is not None:
                # Check email verification
                if not getattr(user, 'is_email_verified', False):
                    messages.error(
                        request,
                        "Please verify your email address before logging in. "
                        "Check your inbox for the verification link.",
                    )
                    return render(request, "customuser/login.html", {"form": form})

                # Log user in
                login(request, user)
                messages.success(request, f"Welcome back, {user.email}!")

                # Redirect logic
                next_page = request.GET.get("next")
                if next_page:
                    return redirect(next_page)
                elif getattr(user, "profile", None) and user.profile.is_complete: # type: ignore
                    return redirect("my_groups")
                else:
                    return redirect("my_groups")
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = CustomUserLoginForm()

    return render(request, "customuser/login.html", {"form": form})



def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def profile_view(request):
    """User profile view"""
    profile = request.user.profile
    return render(request, 'customuser/profile.html', {
        'user': request.user, # type: ignore
        'profile': profile,
    })


@login_required
def profile_edit_view(request):
    """Edit user profile"""
    profile = request.user.profile
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save()
            profile.check_completion()  # Update completion status
            profile.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    return render(request, 'customuser/profile_edit.html', {
        'form': form,
        'profile': profile,
    })


def resend_verification_view(request):
    """Resend email verification"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            if user.is_email_verified:
                messages.info(request, 'This email is already verified.')
            else:
                send_verification_email(request, user)
                messages.success(request, f'Verification email sent to {email}')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'customuser/resend_verification.html')
