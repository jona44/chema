from django.shortcuts import render

# Create your views here.
    # memorials/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden

from group.models import Group, GroupMembership
from customuser.models import Profile
from memorial.forms import MemorialForm
from memorial.models import Memorial



@login_required
def create_memorial_view(request, slug, membership_id):
    """Create a memorial for a deceased group member"""
    group = get_object_or_404(Group, slug=slug)
    membership = get_object_or_404(GroupMembership, id=membership_id, group=group)
    
    # Permission check: Only admins can create memorials
    if not group.is_admin(request.user):
        messages.error(request, "You don't have permission to create memorials.")
        return redirect('group_detail', slug=slug)
    
    # Check if member is actually deceased
    if membership.status != 'deceased':
        messages.error(request, "Memorial can only be created for deceased members.")
        return redirect('group_members', slug=slug)
    
    # Check if memorial already exists for this member in this group
    existing_memorial = Memorial.objects.filter(
        deceased=membership.user.profile,
        associated_group=group
    ).first()
    
    if existing_memorial:
        messages.info(request, "A memorial already exists for this member.")
        return redirect('memorial_detail', pk=existing_memorial.pk)
    
    if request.method == 'POST':
        form = MemorialForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                memorial = form.save(commit=False)
                memorial.deceased = membership.user.profile
                memorial.created_by = request.user
                memorial.associated_group = group
                memorial.save()
                
                # Optionally add the creator as a family admin
                memorial.family_admins.add(request.user)
                
                messages.success(
                    request, 
                    f"Memorial for {membership.user.profile.full_name} has been created successfully."
                )
                return redirect('memorial:memorial_detail', pk=memorial.pk)
    else:
        # Pre-populate form with deceased member's information
        initial_data = {
            'photo': membership.user.profile.profile_picture if membership.user.profile.profile_picture else None,
            'biography': f"In loving memory of {membership.user.profile.full_name}...",
        }
        form = MemorialForm(initial=initial_data)
    
    context = {
        'form': form,
        'group': group,
        'membership': membership,
        'deceased_name': membership.user.profile.full_name,
    }
    
    return render(request, 'memorial/create_memorial.html', context)


@login_required
def memorial_detail_view(request, pk):
    """View a memorial page"""
    memorial = get_object_or_404(Memorial, pk=pk)
    group = memorial.associated_group
    
    # Permission check: Group members or public access
    is_member = GroupMembership.objects.filter(
        group=group,
        user=request.user,
        is_active=True
    ).exists()
    
    is_admin = memorial.is_admin(request.user)
    
    # Check access permissions
    if not memorial.is_public and not is_member:
        messages.error(request, "You don't have access to view this memorial.")
        return redirect('home')
    
    context = {
        'memorial': memorial,
        'group': group,
        'is_admin': is_admin,
        'is_member': is_member,
        'can_view': memorial.is_public or is_member,
    }
    
    return render(request, 'memorial/memorial_detail.html', context)


@login_required
def edit_memorial_view(request, pk):
    """Edit an existing memorial"""
    memorial = get_object_or_404(Memorial, pk=pk)
    
    # Permission check: Only memorial admins
    if not memorial.is_admin(request.user):
        messages.error(request, "You don't have permission to edit this memorial.")
        return redirect('memorial_detail', pk=pk)
    
    if request.method == 'POST':
        form = MemorialForm(request.POST, request.FILES, instance=memorial)
        if form.is_valid():
            form.save()
            messages.success(request, "Memorial updated successfully.")
            return redirect('memorial:memorial_detail', pk=pk)
    else:
        form = MemorialForm(instance=memorial)
    
    context = {
        'form': form,
        'memorial': memorial,
        'group': memorial.associated_group,
        'is_editing': True,
    }
    
    return render(request, 'memorial/create_memorial.html', context)


@login_required
def delete_memorial_view(request, pk):
    """Delete a memorial"""
    memorial = get_object_or_404(Memorial, pk=pk)
    group = memorial.associated_group
    
    # Permission check: Only creator or group creator
    if request.user != memorial.created_by and request.user != group.creator:
        messages.error(request, "You don't have permission to delete this memorial.")
        return redirect('memorial_detail', pk=pk)
    
    if request.method == 'POST':
        deceased_name = memorial.deceased.full_name # type: ignore
        memorial.delete()
        messages.success(request, f"Memorial for {deceased_name} has been deleted.")
        return redirect('group_detail', slug=group.slug)
    
    context = {
        'memorial': memorial,
        'group': group,
    }
    
    return render(request, 'memorials/delete_memorial.html', context)


@login_required
def manage_family_admins_view(request, pk):
    """Manage family admins for a memorial"""
    memorial = get_object_or_404(Memorial, pk=pk)
    
    # Permission check
    if not memorial.is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to manage admins.")
    
    group = memorial.associated_group
    
    # Get all group members who can be added as admins
    available_members = GroupMembership.objects.filter(
        group=group,
        is_active=True,
        status='active'
    ).exclude(
        user__in=memorial.family_admins.all()
    ).select_related('user__profile')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'add' and user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = get_object_or_404(User, id=user_id)
            memorial.family_admins.add(user)
            messages.success(request, f"{user.profile.full_name} added as family admin.") # type: ignore
        
        elif action == 'remove' and user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = get_object_or_404(User, id=user_id)
            if user != memorial.created_by:
                memorial.family_admins.remove(user)
                messages.success(request, f"{user.profile.full_name} removed as family admin.") # pyright: ignore[reportAttributeAccessIssue]
            else:
                messages.error(request, "Cannot remove the memorial creator.")
        
        return redirect('manage_family_admins', pk=pk)
    
    context = {
        'memorial': memorial,
        'group': group,
        'family_admins': memorial.family_admins.all(),
        'available_members': available_members,
    }
    
    return render(request, 'memorial/manage_admins.html', context)


@login_required
def group_memorials_list_view(request, slug):
    """List all memorials for a group"""
    group = get_object_or_404(Group, slug=slug)
    
    # Check if user is a member
    is_member = GroupMembership.objects.filter(
        group=group,
        user=request.user,
        is_active=True
    ).exists()
    
    if not is_member:
        # Show only public memorials for non-members
        memorials = Memorial.objects.filter(
            associated_group=group,
            is_public=True
        ).select_related('deceased', 'created_by')
    else:
        # Show all memorials for members
        memorials = Memorial.objects.filter(
            associated_group=group
        ).select_related('deceased', 'created_by')
    
    context = {
        'group': group,
        'memorials': memorials,
        'is_member': is_member,
        'is_admin': group.is_admin(request.user) if is_member else False,
    }
    
    return render(request, 'memorial/group_memorials.html', context)