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
        # Filter the choices for deceased members to only include those marked as deceased
        deceased_members_queryset = Deceased.objects.filter(group__is_active=True, cont_is_active=True)
        # Set the queryset for deceased_member
        
        form.fields['deceased_member'].queryset = deceased_members_queryset# Filter the choices for contributing members
        
        contributing_members_queryset = Profile.objects.filter(groups__is_active=True).exclude(
        pk__in=Contribution.objects.filter(group__is_active=True).values_list('contributing_member', flat=True)
        )# Set the queryset for contributing_member
        
        form.fields['contributing_member'].queryset = contributing_members_queryset
    
    return render(request, 'condolence/create_contribution.html', {'form': form})



def contribution_detail(request, contribution_id):
    contribution = get_object_or_404(Contribution, id=contribution_id)
    # Get the deceased members related to this contribution
    context = {
        'contribution': contribution,
        }
    return render(request, 'condolence/contribution_detail.html', context)




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


def toggle_deceased(request, deceased_id):
    # Get the deceased being toggled
    deceased_to_toggle = get_object_or_404(Deceased, id=deceased_id)
    
    # Toggle the deceased by setting it to True
    deceased_to_toggle.contributions_open = True
    deceased_to_toggle.save()

    # Deactivate all other deceased
    Deceased.objects.exclude(id=deceased_id).update(contributions_open=False)

    return redirect('home')



def stop_contributions(request, deceased_id):
    # Get the Deceased instance
    deceased = get_object_or_404(Deceased, pk=deceased_id)

    # Call the method to stop contributions
    deceased.stop_contributions()

    # Return a JSON response indicating success
    return HttpResponse('<h1>Contributions for This Deceased Member Closed</h2>')