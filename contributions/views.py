# contributions/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import (
    ContributionCampaign, Contribution, ExpenseRecord, ContributionUpdate
)
from group.models import Group
from memorial.models import Memorial
from .forms import (
    ContributionCampaignForm, ContributionForm, ExpenseRecordForm, 
    ContributionUpdateForm
)


# ============================================================================
# Campaign Management Views
# ============================================================================

@login_required
def campaign_detail_view(request, group_slug): # type: ignore
    """View campaign details and contribution form"""
    group = get_object_or_404(Group, slug=group_slug)
    
    try:
        campaign = ContributionCampaign.objects.get(group=group)
    except ContributionCampaign.DoesNotExist:
        messages.error(request, "No contribution campaign found for this group")
        return redirect('group:detail', slug=group_slug)
    
    # Get recent contributions (anonymous handling)
    recent_contributions = campaign.contributions.filter( # type: ignore
        status='completed'
    ).select_related('contributor', 'contributor__profile').order_by('-completed_at')[:10]
    
    # Get campaign updates
    updates = campaign.updates.filter(is_public=True).order_by('-created_at')[:5] # type: ignore
    
    # Get expense breakdown
    expenses = campaign.expenses.all().order_by('-date_incurred') # type: ignore
    total_expenses = sum(expense.amount for expense in expenses)
    
    # Check if user has contributed
    user_contribution = None
    if request.user.is_authenticated:
        user_contribution = campaign.contributions.filter( # type: ignore
            contributor=request.user,
            status='completed'
        ).first()
    
    context = {
        'group': group,
        'campaign': campaign,
        'recent_contributions': recent_contributions,
        'updates': updates,
        'expenses': expenses,
        'total_expenses': total_expenses,
        'user_contribution': user_contribution,
        'can_manage': group.is_admin(request.user) or (
            campaign.memorial and campaign.memorial.is_admin(request.user)
        ),
    }
    
    return render(request, 'contributions/campaign_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_campaign_view(request, group_slug):
    """Create a new contribution campaign for a group"""
    group = get_object_or_404(Group, slug=group_slug)
    
    # Check if user is admin
    if not group.is_admin(request.user):
        messages.error(request, "Only group administrators can create campaigns")
        return redirect('group:detail', slug=group_slug)
    
    # Check if campaign already exists
    if hasattr(group, 'contribution_campaign'):
        messages.info(request, "A campaign already exists for this group")
        return redirect('contributions:campaign_detail', group_slug=group_slug)
    
    if request.method == 'POST':
        form = ContributionCampaignForm(request.POST, group=group)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.group = group
            campaign.created_by = request.user
            campaign.status = 'active' # Explicitly set status on creation
            
            # Link memorial if selected
            memorial = form.cleaned_data.get('memorial')
            if memorial:
                campaign.memorial = memorial
            
            campaign.save()
            
            messages.success(request, "Contribution campaign created successfully!")
            return redirect('contributions:campaign_detail', group_slug=group_slug)
    else:
        # Pre-fill some defaults
        initial = {
            'title': f"Support for {group.name}",
            'public_updates': True,
        }
        form = ContributionCampaignForm(initial=initial, group=group)
    
    # Get memorials for context
    from memorial.models import Memorial
    memorials = Memorial.objects.filter(associated_group=group)
    
    context = {
        'group': group,
        'form': form,
        'memorials': memorials,
        'has_multiple_memorials': memorials.count() > 1,
    }
    
    return render(request, 'contributions/create_campaign.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def edit_campaign_view(request, group_slug):
    """Edit campaign details"""
    group = get_object_or_404(Group, slug=group_slug)
    campaign = get_object_or_404(ContributionCampaign, group=group)
    
    # Check permissions
    if not group.is_admin(request.user):
        messages.error(request, "Only administrators can edit campaigns")
        return redirect('contributions:campaign_detail', group_slug=group_slug)
    
    if request.method == 'POST':
        form = ContributionCampaignForm(request.POST, instance=campaign, group=group)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign updated successfully!")
            return redirect('contributions:campaign_detail', group_slug=group_slug)
    else:
        form = ContributionCampaignForm(instance=campaign, group=group)
    
    context = {
        'group': group,
        'campaign': campaign,
        'form': form,
    }
    
    return render(request, 'contributions/edit_campaign.html', context)


# ============================================================================
# Contribution (Donation) Views
# ============================================================================

@require_http_methods(["GET", "POST"])
def make_contribution_view(request, group_slug):
    """Make a contribution to the campaign"""
    group = get_object_or_404(Group, slug=group_slug)
    campaign = get_object_or_404(ContributionCampaign, group=group)
    
    if not campaign.can_contribute():
        messages.error(request, "This campaign is no longer accepting contributions")
        return redirect('contributions:campaign_detail', group_slug=group_slug)
    
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.campaign = campaign
            
            
            # Set contributor if logged in
            if request.user.is_authenticated:
                contribution.contributor = request.user
                if not contribution.contributor_name:
                    contribution.contributor_name = request.user.profile.full_name
            
            # For now, mark as completed (integrate payment gateway later)
            # In production, status would be 'pending' until payment confirmed
            contribution.status = 'pending'  # Change to 'completed' after payment
            contribution.save()
            
            messages.success(request, "Thank you for your contribution!")
            
            # Redirect to payment page (or success page for now)
            return redirect('contributions:contribution_success', 
                        group_slug=group_slug, 
                        contribution_id=contribution.id)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'contributor_name': request.user.profile.full_name,
                'contributor_email': request.user.email,
            }
        form = ContributionForm(initial=initial)
    
    context = {
        'group': group,
        'campaign': campaign,
        'form': form,
    }
    
    return render(request, 'contributions/make_contribution.html', context)


def contribution_success_view(request, group_slug, contribution_id):
    """Success page after making a contribution"""
    group = get_object_or_404(Group, slug=group_slug)
    contribution = get_object_or_404(Contribution, id=contribution_id)
    
    context = {
        'group': group,
        'contribution': contribution,
        'campaign': contribution.campaign,
    }
    
    return render(request, 'contributions/contribution_success.html', context)


@login_required
def my_contributions_view(request):
    """View all contributions made by the current user"""
    contributions = Contribution.objects.filter(
        contributor=request.user
    ).select_related('campaign', 'campaign__group').order_by('-created_at')
    
    total_contributed = sum(
        c.amount for c in contributions if c.status == 'completed'
    )
    
    context = {
        'contributions': contributions,
        'total_contributed': total_contributed,
    }
    
    return render(request, 'contributions/my_contributions.html', context)


# ============================================================================
# Campaign Management - Updates & Expenses
# ============================================================================

@login_required
@require_http_methods(["GET", "POST"])
def create_update_view(request, group_slug):
    """Create a campaign update"""
    group = get_object_or_404(Group, slug=group_slug)
    campaign = get_object_or_404(ContributionCampaign, group=group)
    
    if not group.is_admin(request.user):
        messages.error(request, "Only administrators can post updates")
        return redirect('contributions:campaign_detail', group_slug=group_slug)
    
    if request.method == 'POST':
        form = ContributionUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            update = form.save(commit=False)
            update.campaign = campaign
            update.created_by = request.user
            update.save()
            
            # TODO: Send notifications if notify_contributors is True
            
            messages.success(request, "Update posted successfully!")
            return redirect('contributions:campaign_detail', group_slug=group_slug)
    else:
        form = ContributionUpdateForm()
    
    context = {
        'group': group,
        'campaign': campaign,
        'form': form,
    }
    
    return render(request, 'contributions/create_update.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def record_expense_view(request, group_slug):
    """Record an expense for the campaign"""
    group = get_object_or_404(Group, slug=group_slug)
    campaign = get_object_or_404(ContributionCampaign, group=group)
    
    if not group.is_admin(request.user):
        messages.error(request, "Only administrators can record expenses")
        return redirect('contributions:campaign_detail', group_slug=group_slug)
    
    if request.method == 'POST':
        form = ExpenseRecordForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.campaign = campaign
            expense.recorded_by = request.user
            expense.save()
            
            messages.success(request, "Expense recorded successfully!")
            return redirect('contributions:campaign_detail', group_slug=group_slug)
    else:
        form = ExpenseRecordForm()
    
    context = {
        'group': group,
        'campaign': campaign,
        'form': form,
    }
    
    return render(request, 'contributions/record_expense.html', context)


# ============================================================================
# HTMX/AJAX Views
# ============================================================================

@login_required
@require_http_methods(["POST"])
def quick_contribute_view(request, group_slug):
    """Quick contribution via HTMX"""
    group = get_object_or_404(Group, slug=group_slug)
    campaign = get_object_or_404(ContributionCampaign, group=group)
    
    if not campaign.can_contribute():
        return JsonResponse({'error': 'Campaign closed'}, status=400)
    
    amount = request.POST.get('amount')
    message = request.POST.get('message', '')
    is_anonymous = request.POST.get('is_anonymous') == 'on'
    
    try:
        amount = Decimal(amount)
        if amount < Decimal('1.00'):
            return JsonResponse({'error': 'Minimum contribution is 1.00'}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid amount'}, status=400)
    
    contribution = Contribution.objects.create(
        campaign=campaign,
        contributor=request.user,
        contributor_name=request.user.profile.full_name if hasattr(request.user, 'profile') else request.user.email,
        contributor_email=request.user.email,
        amount=amount,
        message=message,
        is_anonymous=is_anonymous,
        status='pending',  # Would be 'pending' until payment confirmed
    )
    
    html = render_to_string('contributions/partials/contribution_item.html', {
        'contribution': contribution,
    }, request=request)
    
    return HttpResponse(html)


@login_required
def campaign_stats_view(request, group_slug):
    """Get campaign statistics via HTMX"""
    group = get_object_or_404(Group, slug=group_slug)
    campaign = get_object_or_404(ContributionCampaign, group=group)
    
    stats = {
        'current_amount': float(campaign.current_amount),
        'target_amount': float(campaign.target_amount),
        'progress_percentage': float(campaign.progress_percentage),
        'contributor_count': campaign.contributor_count,
        'remaining_amount': float(campaign.remaining_amount),
    }
    
    return JsonResponse(stats)


def contribution_widget_view(request, group_slug):
    """Embeddable contribution widget for group pages"""
    group = get_object_or_404(Group, slug=group_slug)
    
    try:
        campaign = ContributionCampaign.objects.get(group=group, status='active')
    except ContributionCampaign.DoesNotExist:
        return HttpResponse('')  # Return empty if no campaign
    
    context = {
        'group': group,
        'campaign': campaign,
    }
    
    return render(request, 'contributions/widgets/campaign_widget.html', context)