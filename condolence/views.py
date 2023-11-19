from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from condolence.forms import *
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from chema.models import *




def create_contribution(request):
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            current_group = Group.objects.get(is_active=True)
            group_admin = current_group.admin  # Assuming 'admin' is the ForeignKey to Profile
            
            # Check if user is part of AdminGroup
            if not request.user.groups.filter(name="Admin").exists():
                # Redirect the user to somewhere else - add your URL here
               messages.error(request, "You are not an admin of this group.")
            
            amount = form.cleaned_data['amount']
            deceased_member = form.cleaned_data['deceased_member']
            contributing_member = form.cleaned_data['contributing_member']
            
            contribution = Contribution(
                group=current_group,
                amount=amount,
                contributing_member=contributing_member,
                group_admin=request.user.profile,
                deceased_member=deceased_member
            )
            contribution.save()

            # Use the add method to set deceased members
            return redirect('contribution_detail', contribution.id)
    else:
        form = ContributionForm()
    
    return render(request, 'condolence/create_contribution.html', {'form': form})


def contribution_detail(request, contribution_id):
    contribution = get_object_or_404(Contribution, id=contribution_id)

    # Get the deceased members related to this contribution
   

    context = {
        'contribution': contribution,
       
    }

    return render(request, 'condolence/contribution_detail.html', context)


def contributions_list(request):
    contributions = Contribution.objects.dates()
  
    context = {
        'contributions': contributions,
        
    }

    return render(request, 'chema/home.html', context)

def deceased(request):
    active_group = Group.objects.filter(is_active=True).first()
    group_admin = Profile.objects.filter(groupmembership__is_admin=True, groups=active_group)
    
    if request.method == 'POST':
        form = DeceasedForm(request.POST)
        if form.is_valid():
            deceased=form.save(commit=False) 
            deceased.group= active_group
            deceased.group_admin= request.user.profile
            deceased.save()
            messages.success(request, "Group member has been marked as Deceased!")
            return redirect('group_detail_view', active_group.id)
    else:
        form = DeceasedForm()
    return render(request, 'condolence/deceased.html', {'form':form,'active_group':active_group} )

