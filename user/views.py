from django.shortcuts import render,redirect,get_object_or_404
from django .contrib.auth.models import User
from .forms import UserUpdateForm, ProfileUpdateForm,UserRegisterForm
from django.contrib import messages
from .forms import UserUpdateForm, ProfileUpdateForm,UserRegisterForm
from django.contrib.auth.decorators import login_required
from .models import Profile
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





