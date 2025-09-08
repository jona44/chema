from django.shortcuts import render, get_object_or_404
from .models import ContributionCampaign
from group.models import Group

def campaign_detail_view(request, group_slug):
    group = get_object_or_404(Group, slug=group_slug)
    campaign = get_object_or_404(ContributionCampaign, group=group)
    
    context = {
        'group': group,
        'campaign': campaign,
    }
    
    return render(request, 'contributions/campaign_detail.html', context)