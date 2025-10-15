# groups/views.py
from datetime import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.mail import send_mail
from customuser.models import Profile
from feeds.models import Feed
from group.forms import GroupCreationForm, GroupInvitationForm, GroupJoinForm, GroupSearchForm, GroupEditForm, MarkDeceasedForm
from .models import Group, GroupMembership, GroupInvitation, Category
from datetime import timezone
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string



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
    invitation_id = request.GET.get('invitation')

    # ---------- Handle Invitation Flow ----------
    if invitation_id:
        try:
            invitation = GroupInvitation.objects.get(id=invitation_id, group=group)
            if invitation.is_expired:
                messages.error(request, "This invitation has expired.")
                return redirect('group_detail', slug=slug)
            
            if invitation.invited_email != request.user.email:
                messages.error(request, "This invitation is not for you.")
                return redirect('group_detail', slug=slug)

            success, message = invitation.accept()
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
            return redirect('group_detail', slug=slug)

        except GroupInvitation.DoesNotExist:
            messages.error(request, "Invalid invitation link.")
            return redirect('group_detail', slug=slug)

    # ---------- Permission Check ----------
    can_join, message = group.can_join(request.user)
    if not can_join:
        messages.error(request, message)
        return redirect('group_detail', slug=slug)

    # ---------- Prevent Duplicate Membership ----------
    existing_membership = GroupMembership.objects.filter(group=group, user=request.user).first()
    if existing_membership:
        if existing_membership.status == 'active':
            messages.info(request, f"You are already an active member of {group.name}.")
        elif existing_membership.status == 'pending':
            messages.info(request, f"Your request to join {group.name} is still pending approval.")
        else:
            messages.warning(request, f"You already have a membership record in {group.name}.")
        return redirect('group_detail', slug=slug)

    # ---------- Handle Join Form ----------
    if request.method == 'POST':
        form = GroupJoinForm(request.POST)
        if form.is_valid():
            join_message = form.cleaned_data.get('message', '')

            status = 'pending' if group.requires_approval else 'active'

            membership = GroupMembership.objects.create(
                group=group,
                user=request.user,
                status=status,
                join_message=join_message,
                approved_at=timezone.now() if status == 'active' else None,  # type: ignore
                approved_by=group.creator if status == 'active' else None,
            )

            if status == 'active':
                messages.success(request, f"Welcome to {group.name}!")
            else:
                messages.info(
                    request,
                    f"Your request to join {group.name} has been sent for approval."
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
    # Active memberships (joined groups)
    memberships = (
        GroupMembership.objects.filter(
            user=request.user,
            is_active=True,
            status="active"
        )
        .select_related("group")
        .order_by("-joined_at")
    )

    # Groups user created
    created_groups = (
        Group.objects.filter(
            creator=request.user,
            is_active=True
        )
        .annotate(
            num_members=Count("memberships", filter=Q(memberships__is_active=True))
        )
    )

    # Build unified list
    my_groups = []

    # Created groups (tag them as creator)
    for group in created_groups:
        my_groups.append({
            "group": group,
            "role": "creator",
            "joined_at": group.created_at,
        })

    # Membership groups (exclude duplicates if user also creator)
    for membership in memberships:
        if membership.group not in [g["group"] for g in my_groups]:
            my_groups.append({
                "group": membership.group,
                "role": membership.role,
                "joined_at": membership.joined_at,
            })

    # Pending memberships
    pending_groups = GroupMembership.objects.filter(
        user=request.user,
        is_active=True,
        status="pending"
    ).select_related("group").order_by("-joined_at")

    context = {
        "my_groups": my_groups,
        "pending_groups": pending_groups,
        "total_groups": len(my_groups),
    }
    return render(request, "group/my_groups.html", context)


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



# In your views.py (or wherever mark_deceased_view is located)
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from .models import  Group, GroupMembership # Assuming your models are here
from .forms import MarkDeceasedForm # Your form

@login_required
def mark_deceased_view(request, slug, pk):
    """Mark a member as deceased"""
    group = get_object_or_404(Group, slug=slug)
    profile = get_object_or_404(Profile, pk=pk)
    
    # Check if user has permission to manage this group
    if not group.is_admin(request.user):
        messages.error(request, "You don't have permission to manage members.")
        return redirect('group_detail', slug=slug)
    
    # Get the membership for this user in this specific group
    try:
        membership = GroupMembership.objects.get(user=profile.user, group=group)
    except GroupMembership.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == "POST":
        form = MarkDeceasedForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.is_deceased = True
            profile.save()

            # Update the membership status
            membership.status = 'deceased'
            membership.is_active = False
            membership.can_post = False
            membership.can_comment = False
            membership.save()

            # Re-render the table row partial
            html = render_to_string(
                "group/manage/partials/member_row.html",  # Fixed path
                {
                    "membership": membership, 
                    "group": group, 
                    "is_creator": group.creator == request.user
                },
                request=request,
            )
            return HttpResponse(html)
    else:
        form = MarkDeceasedForm(instance=profile)

    return render(
        request,
        "group/mark_deceased_modal.html",  # Fixed path
        {"form": form, "profile": profile, "group": group},
    )