# groups/views.py
from datetime import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.mail import send_mail
from group.forms import GroupCreationForm, GroupInvitationForm, GroupJoinForm, GroupSearchForm, GroupEditForm
from group.forms import GroupCreationForm, GroupInvitationForm, GroupJoinForm, GroupSearchForm
from .models import Group, GroupMembership, GroupInvitation, Category



@login_required
def get_started_view(request):
    """Main landing page for authenticated users with complete profiles"""
    # Get some featured groups and categories for display
    featured_groups = Group.objects.filter(
        privacy='public', 
        is_active=True
    ).annotate(
        num_members=Count('memberships', filter=Q(memberships__is_active=True))
    ).order_by('-num_members')[:6]
    
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    # User's current groups
    user_groups = Group.objects.filter(
        memberships__user=request.user,
        memberships__is_active=True
    ).annotate(
        num_members=Count('memberships', filter=Q(memberships__is_active=True))
    ).order_by('name')
    
    context = {
        'user': request.user,
        'featured_groups': featured_groups,
        'categories': categories,
        'user_groups': user_groups,
        'total_groups': Group.objects.filter(is_active=True).count(),
        'total_members': GroupMembership.objects.filter(is_active=True).values('user').distinct().count(),
    }
    
    return render(request, 'group/get_started.html', context)
from datetime import timezone
from django.utils import timezone

@login_required
def create_group_view(request):
    """Create a new group"""
    if request.method == 'POST':
        form = GroupCreationForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            
            # Auto-add creator as admin member
            GroupMembership.objects.create(
                group=group,
                user=request.user,
                role='admin',
                status='active',
                approved_at=timezone.now(),
                approved_by=request.user
            )
            
            messages.success(
                request, 
                f'Group "{group.name}" created successfully! You are now the admin.'
            )
            return redirect('group_detail', slug=group.slug)
    else:
        form = GroupCreationForm()
    
    return render(request, 'group/create_group.html', {
        'form': form,
        'categories': Category.objects.filter(is_active=True)
    })


def browse_groups_view(request):
    """Browse and search groups"""
    groups = Group.objects.filter(is_active=True, privacy='public').annotate(
        num_members=Count('memberships', filter=Q(memberships__is_active=True))
    )
    
    # Search functionality
    search_form = GroupSearchForm(request.GET)
    if search_form.is_valid():
        query = search_form.cleaned_data.get('query')
        category = search_form.cleaned_data.get('category')
        city = search_form.cleaned_data.get('city')
        
        if query:
            groups = groups.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query)
            )
        
        if category:
            groups = groups.filter(category=category)
        
        if city:
            groups = groups.filter(city__icontains=city)
    
    # Pagination
    paginator = Paginator(groups.order_by('-last_activity'), 12)
    page_number = request.GET.get('page')
    page_groups = paginator.get_page(page_number)
    
    context = {
        'groups': page_groups,
        'search_form': search_form,
        'categories': Category.objects.filter(is_active=True),
        'total_results': groups.count(),
    }
    
    return render(request, 'group/browse_groups.html', context)





@login_required
def join_group_view(request, slug):
    """Join a group"""
    group = get_object_or_404(Group, slug=slug, is_active=True)
    
    can_join, message = group.can_join(request.user)
    if not can_join:
        messages.error(request, message)
        return redirect('group_detail', slug=slug)
    
    if request.method == 'POST':
        form = GroupJoinForm(request.POST)
        if form.is_valid():
            join_message = form.cleaned_data.get('message', '')
            
            # Create membership
            status = 'pending' if group.requires_approval else 'active'
            membership = GroupMembership.objects.create(
                group=group,
                user=request.user,
                status=status,
                join_message=join_message,
                approved_at=timezone.now() if status == 'active' else None, # type: ignore
                approved_by=group.creator if status == 'active' else None
            )
            
            if status == 'active':
                messages.success(request, f'Welcome to {group.name}!')
            else:
                messages.info(
                    request, 
                    f'Your request to join {group.name} has been sent for approval.'
                )
            
            return redirect('group_detail', slug=slug)
    else:
        form = GroupJoinForm()
    
    return render(request, 'group/join_group.html', {
        'group': group,
        'form': form,
    })


@login_required
def my_groups_view(request):
    """User's groups dashboard"""
    memberships = GroupMembership.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('group').order_by('-joined_at')
    
    # Separate by status
    active_groups = memberships.filter(status='active')
    pending_groups = memberships.filter(status='pending')
    
    # Groups user created
    created_groups = Group.objects.filter(
        creator=request.user,
        is_active=True
    ).annotate(
        num_members=Count('memberships', filter=Q(memberships__is_active=True))
    )
    
    context = {
        'active_memberships': active_groups,
        'pending_memberships': pending_groups,
        'created_groups': created_groups,
        'total_groups': active_groups.count(),
    }
    
    return render(request, 'group/my_groups.html', context)


@login_required
def leave_group_view(request, slug):
    """Leave a group"""
    group = get_object_or_404(Group, slug=slug)
    
    try:
        membership = GroupMembership.objects.get(
            group=group,
            user=request.user,
            is_active=True
        )
        
        if request.user == group.creator:
            messages.error(
                request, 
                "As the group creator, you cannot leave the group. You can transfer ownership or delete the group instead."
            )
            return redirect('group_detail', slug=slug)
        
        if request.method == 'POST':
            membership.is_active = False
            membership.save()
            
            messages.success(request, f'You have left {group.name}.')
            return redirect('my_groups')
        
        return render(request, 'group/leave_group.html', {
            'group': group,
            'membership': membership,
        })
        
    except GroupMembership.DoesNotExist:
        messages.error(request, "You are not a member of this group.")
        return redirect('group_detail', slug=slug)


# AJAX view for search suggestions
def group_search_suggestions(request):
    """AJAX endpoint for search suggestions"""
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        groups = Group.objects.filter(
            Q(name__icontains=query) | Q(tags__icontains=query),
            is_active=True,
            privacy='public'
        ).annotate(
            num_members=Count('memberships', filter=Q(memberships__is_active=True))
        )[:5]
        
        suggestions = [
            {
                'name': group.name,
                'slug': group.slug,
                'member_count': group.num_members, # type: ignore
                'category': group.category.name if group.category else None,
            }
            for group in groups
        ]
    
    return JsonResponse({'suggestions': suggestions})




@login_required
def group_edit_view(request, slug):
    """Edit group settings"""
    group = get_object_or_404(Group, slug=slug, is_active=True)
    
    if not group.is_admin(request.user):
        messages.error(request, "You don't have permission to edit this group.")
        return redirect('group_detail', slug=slug)
    
    if request.method == 'POST':
        form = GroupEditForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            updated_group = form.save()
            messages.success(request, 'Group settings updated successfully!')
            return redirect('group_manage', slug=updated_group.slug)
    else:
        form = GroupEditForm(instance=group)
    
    return render(request, 'group/manage/edit.html', {
        'form': form,
        'group': group,
        'categories': Category.objects.filter(is_active=True)
    })



@login_required
def approve_member_view(request, slug, membership_id):
    """Approve a pending member"""
    group = get_object_or_404(Group, slug=slug, is_active=True)
    membership = get_object_or_404(GroupMembership, id=membership_id, group=group)
    
    if not group.is_admin(request.user):
        messages.error(request, "You don't have permission to approve members.")
        return redirect('group_detail', slug=slug)
    
    if request.method == 'POST':
        if membership.status == 'pending':
            membership.approve(request.user)
            
            # Send notification email to the user
            try:
                send_mail(
                    subject=f'Welcome to {group.name}!',
                    message=f'Your request to join {group.name} has been approved.',
                    from_email=None,  # Use DEFAULT_FROM_EMAIL
                    recipient_list=[membership.user.email],
                    fail_silently=True,
                )
            except:
                pass  # Don't fail if email sending fails
            
            messages.success(request, f'{membership.user.profile.full_name or membership.user.email} has been approved!')
        else:
            messages.info(request, 'This member has already been processed.')
    
    return redirect('group_manage_members', slug=slug)


@login_required
def reject_member_view(request, slug, membership_id):
    """Reject a pending member"""
    group = get_object_or_404(Group, slug=slug, is_active=True)
    membership = get_object_or_404(GroupMembership, id=membership_id, group=group)
    
    if not group.is_admin(request.user):
        messages.error(request, "You don't have permission to reject members.")
        return redirect('group_detail', slug=slug)
    
    if request.method == 'POST':
        if membership.status == 'pending':
            membership.delete()
            messages.success(request, 'Member request has been rejected.')
        else:
            messages.info(request, 'This member has already been processed.')
    
    return redirect('group_manage_members', slug=slug)


@login_required
def remove_member_view(request, slug, membership_id):
    """Remove a member from the group"""
    group = get_object_or_404(Group, slug=slug, is_active=True)
    membership = get_object_or_404(GroupMembership, id=membership_id, group=group)
    
    if not group.is_admin(request.user):
        messages.error(request, "You don't have permission to remove members.")
        return redirect('group_detail', slug=slug)
    
    # Can't remove the creator
    if membership.user == group.creator:
        messages.error(request, "Cannot remove the group creator.")
        return redirect('group_manage_members', slug=slug)
    
    if request.method == 'POST':
        user_name = membership.user.profile.full_name or membership.user.email
        membership.is_active = False
        membership.save()
        
        # Send notification email
        try:
            send_mail(
                subject=f'Removed from {group.name}',
                message=f'You have been removed from the group {group.name}.',
                from_email=None,
                recipient_list=[membership.user.email],
                fail_silently=True,
            )
        except:
            pass
        
        messages.success(request, f'{user_name} has been removed from the group.')
    
    return redirect('group_manage_members', slug=slug)


@login_required
def change_member_role_view(request, slug, membership_id):
    """Change a member's role"""
    group = get_object_or_404(Group, slug=slug, is_active=True)
    membership = get_object_or_404(GroupMembership, id=membership_id, group=group)
    
    if not group.is_admin(request.user):
        messages.error(request, "You don't have permission to change member roles.")
        return redirect('group_detail', slug=slug)
    
    # Only creator can assign admin roles
    if request.user != group.creator and request.POST.get('role') == 'admin':
        messages.error(request, "Only the group creator can assign admin roles.")
        return redirect('group_manage_members', slug=slug)
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in ['member', 'moderator', 'admin']:
            old_role = membership.role
            membership.role = new_role
            membership.save()
            
            user_name = membership.user.profile.full_name or membership.user.email
            messages.success(
                request, 
                f'{user_name} role changed from {old_role} to {new_role}.'
            )
        else:
            messages.error(request, "Invalid role specified.")
    
    return redirect('group_manage_members', slug=slug)

