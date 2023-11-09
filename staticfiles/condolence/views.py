from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from condolence.forms import ContributionForm
from .models import Contribution
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
            deceased_members = form.cleaned_data['deceased_member']
            contributing_member = form.cleaned_data['contributing_member']
            
            contribution = Contribution(
                group=current_group,
                amount=amount,
                contributing_member=contributing_member,
                group_admin=group_admin
            )
            contribution.save()

            # Use the add method to set deceased members
            contribution.deceased_member.add(*deceased_members)
            
            return redirect('contribution_detail', contribution.id)
    else:
        form = ContributionForm()
    
    return render(request, 'condolence/create_contribution.html', {'form': form})


def contribution_detail(request, contribution_id):
    contribution = get_object_or_404(Contribution, id=contribution_id)

    # Get the deceased members related to this contribution
    deceased_members = contribution.deceased_member.all()

    context = {
        'contribution': contribution,
        'deceased_members': deceased_members,
    }

    return render(request, 'condolence/contribution_detail.html', context)


def contributions_list(request):
    contributions = Contribution.objects.all()
    list_count = Contribution.objects.all().count()# You can filter or order the contributions as needed
    print(list_count)
    context = {
        'contributions': contributions,
        'list_count': list_count
    }

    return render(request, 'chema/home.html', context)



    
