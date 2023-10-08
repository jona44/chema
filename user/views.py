from django.shortcuts import render,redirect,get_object_or_404
from django .contrib.auth.models import User
from .forms import UserUpdateForm, ProfileUpdateForm,UserRegisterForm
from django.contrib import messages
from .forms import UserUpdateForm, ProfileUpdateForm,UserRegisterForm
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import DeceasedProfileForm
from chema.models import Group


# Create your views here.
@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'user/profile.html', context)


def user_register(request):
   
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account has been created{username}!')
            return redirect('choice')
    else:
        form = UserRegisterForm()
    return render(request, 'user/user-register.html', {'form': form})

 


def update_deceased_status(request, profile_id):
    print("Received profile_id:", profile_id)  
    # Retrieve the Profile instance based on the profile_id or raise a 404 error
    profile = get_object_or_404(Profile, id=profile_id)

    # Check if the user is a group admin for any group
    user = request.user

    # Here, you are checking if the user is a group admin by filtering the Group model.
    # Make sure the logic to determine if a user is a group admin is accurate.
    # This logic assumes that a user is a group admin if they are listed in the admins_as_members field of any group.
    is_group_admin = Group.objects.filter(admins_as_members=profile).exists()

    if not is_group_admin:
        # If the user is not a group admin, you can handle this as per your requirements.
        # For example, you can display an error message or redirect them to a different page.
        return render(request, 'access_denied.html')  # Create an 'access_denied.html' template for this purpose

    if request.method == 'POST':
        form = DeceasedProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('member_detail', pk=profile.user.id)
    else:
        form = DeceasedProfileForm(instance=profile)

    return render(request, 'user/update_deceased_status.html', {'form': form, 'profile': profile})
