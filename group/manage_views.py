# groups/views.py
from django.utils import timezone
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
def group_settings_view(request, slug):
    """Advanced group settings"""
    group = get_object_or_404(Group, slug=slug, is_active=True)
    
    if request.user != group.creator:
        messages.error(request, "Only the group creator can access advanced settings.")
        return redirect('group_detail', slug=slug)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'transfer_ownership':
            new_owner_email = request.POST.get('new_owner_email')
            try:
                from customuser.models import CustomUser
                new_owner = CustomUser.objects.get(email=new_owner_email)
                
                # Check if new owner is a member
                if not group.is_member(new_owner):
                    messages.error(request, "New owner must be a group member.")
                else:
                    # Transfer ownership
                    group.creator = new_owner
                    group.save()
                    
                    # Make sure new owner is admin
                    membership = GroupMembership.objects.get(group=group, user=new_owner)
                    membership.role = 'admin'
                    membership.save()
                    
                    messages.success(request, f'Ownership transferred to {new_owner.email}')
                    return redirect('group_detail', slug=slug)
                    
            except CustomUser.DoesNotExist:
                messages.error(request, "User not found.")
        
        elif action == 'deactivate_group':
            if request.POST.get('confirm_deactivate') == 'DEACTIVATE':
                group.is_active = False
                group.save()
                messages.success(request, 'Group has been deactivated.')
                return redirect('my_groups')
            else:
                messages.error(request, 'Please type "DEACTIVATE" to confirm.')
        
        elif action == 'delete_group':
            if request.POST.get('confirm_delete') == 'DELETE':
                group_name = group.name
                group.delete()
                messages.success(request, f'Group "{group_name}" has been deleted.')
                return redirect('my_groups')
            else:
                messages.error(request, 'Please type "DELETE" to confirm.')
    
    context = {
        'group': group,
        'member_count': group.member_count,
    }
    
    return render(request, 'group/manage/settings.html', context)



@login_required
def group_invitations_view(request, slug):
    """Manage group invitations"""
    group = get_object_or_404(Group, slug=slug, is_active=True)
    
    if not group.is_admin(request.user):
        messages.error(request, "You don't have permission to manage invitations.")
        return redirect('group_detail', slug=slug)
    
    # Handle invitation form
    if request.method == 'POST':
        form = GroupInvitationForm(request.POST)
        if form.is_valid():
            emails = form.cleaned_data['emails']
            message = form.cleaned_data.get('message', '')
            
            sent_count = 0
            for email in emails:
                # Check if user already invited or is member
                if GroupInvitation.objects.filter(group=group, invited_email=email, status='pending').exists():
                    continue
                
                if GroupMembership.objects.filter(group=group, user__email=email, is_active=True).exists():
                    continue
                
                # Create invitation
                invitation = GroupInvitation.objects.create(
                    group=group,
                    invited_by=request.user,
                    invited_email=email,
                    message=message,
                    expires_at=timezone.now() + timezone.timedelta(days=7)
                )
                
                # Send invitation email
                try:
                    invitation_link = request.build_absolute_uri(
                        f'/groups/{group.slug}/join/?invitation={invitation.id}'
                    )
                    
                    send_mail(
                        subject=f'Invitation to join {group.name}',
                        message=f'You\'ve been invited to join {group.name}. Click here: {invitation_link}',
                        from_email=None,
                        recipient_list=[email],
                        fail_silently=True,
                    )
                    sent_count += 1
                except:
                    pass
            
            if sent_count > 0:
                messages.success(request, f'{sent_count} invitation(s) sent successfully!')
            else:
                messages.info(request, 'No new invitations were sent.')
            
            return redirect('group_manage_invitations', slug=slug)
    else:
        form = GroupInvitationForm()
    
    # Get existing invitations (using related_name from Group model)
    invitations = GroupInvitation.objects.filter(group=group).order_by('-created_at')
    
    context = {
        'group': group,
        'form': form,
        'invitations': invitations,
    }
    
    return render(request, 'group/manage/invitations.html', context)


@login_required
def group_members_view(request, slug):
    """Manage group members"""
    group = get_object_or_404(Group, slug=slug, is_active=True)
    
    if not group.is_admin(request.user):
        messages.error(request, "You don't have permission to manage members.")
        return redirect('group_detail', slug=slug)
    
    # Filter and search members
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', 'active')
    
    memberships = group.memberships.filter(is_active=True).select_related('user__profile')# type: ignore
    
    if search_query:
        memberships = memberships.filter(
            Q(user__email__icontains=search_query) |
            Q(user__profile__first_name__icontains=search_query) |
            Q(user__profile__surname__icontains=search_query)
        )
    
    if role_filter:
        memberships = memberships.filter(role=role_filter)
    
    if status_filter:
        memberships = memberships.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(memberships.order_by('-joined_at'), 20)
    page_number = request.GET.get('page')
    page_memberships = paginator.get_page(page_number)
    
    context = {
        'group': group,
        'memberships': page_memberships,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'is_creator': request.user == group.creator,
    }
    
    return render(request, 'group/manage/members.html', context)


@login_required
def group_manage_view(request, slug):
    """Main group management dashboard"""
    group = get_object_or_404(Group, slug=slug, is_active=True)
    
    # Check if user has admin permissions
    if not group.is_admin(request.user):
        messages.error(request, "You don't have permission to manage this group.")
        return redirect('group_detail', slug=slug)
    
    # Get membership statistics
    total_members = group.memberships.filter(is_active=True).count() # type: ignore
    active_members = group.memberships.filter(is_active=True, status='active').count() # type: ignore
    pending_members = group.memberships.filter(is_active=True, status='pending').count() # type: ignore
    
    # Recent activity
    recent_memberships = group.memberships.filter(# type: ignore
        is_active=True# type: ignore
    ).select_related('user__profile').order_by('-joined_at')[:10]
    
    # Pending approval requests
    pending_requests = group.memberships.filter(# type: ignore
        status='pending', 
        is_active=True
    ).select_related('user__profile').order_by('-joined_at')
    
    context = {
        'group': group,
        'total_members': total_members,
        'active_members': active_members,
        'pending_members': pending_members,
        'recent_memberships': recent_memberships,
        'pending_requests': pending_requests,
        'is_creator': request.user == group.creator,
    }
    
    return render(request, 'group/manage/dashboard.html', context)


def group_detail_view(request, slug):
    """Group detail page"""
    group = get_object_or_404(
        Group.objects.annotate(
            num_members=Count('memberships', filter=Q(memberships__is_active=True))
        ),
        slug=slug,
        is_active=True
    )
    
    # Check user's relationship with group
    user_membership = None
    can_join = False
    join_message = ""

    if request.user.is_authenticated:
        try:
            user_membership = GroupMembership.objects.get(
                group=group, 
                user=request.user
            )
        except GroupMembership.DoesNotExist:
            can_join, join_message = group.can_join(request.user)
    
    # Get recent members
    recent_members = GroupMembership.objects.filter(
        group=group, 
        is_active=True,
        status='active'
    ).select_related('user__profile').order_by('-joined_at')[:10]
    
    context = {
        'group': group,
        'user_membership': user_membership,
        'can_join': can_join,
        'join_message': join_message,
        'recent_members': recent_members,
        'is_admin': group.is_admin(request.user) if request.user.is_authenticated else False,
    }
    
    return render(request, 'group/manage/group_detail.html', context)


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


