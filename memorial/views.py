# memorial/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import (
    Memorial, Post, Comment, PostLike, CommentLike, 
    CondolenceMessage, FuneralUpdate, PostImage
)
from .forms import (
    MemorialCreationForm, PostForm, CommentForm, 
    CondolenceForm, FuneralUpdateForm
) 
from group.models import Group, GroupMembership


def memorial_detail_view(request, pk):
    """Main memorial page - central hub for remembrance"""
    memorial = get_object_or_404(Memorial, pk=pk)
    
    # Check permissions
    if not memorial.is_public:
        if not request.user.is_authenticated:
            messages.error(request, "This memorial is private. Please log in.")
            return redirect('login')
        
        # Check if user is group member
        if not memorial.associated_group.is_member(request.user) and not memorial.is_admin(request.user):
            messages.error(request, "You don't have permission to view this memorial.")
            return redirect('browse_groups')
    
    # Get recent posts with engagement data
    posts = Post.objects.filter(
        memorial=memorial
    ).select_related(
        'author__profile'
    ).prefetch_related(
        'images', 'likes', 'comments__author__profile'
    ).order_by('-is_pinned', '-created_at')[:10]
    
    # Get recent condolences
    condolences = CondolenceMessage.objects.filter(
        memorial=memorial,
        is_approved=True
    ).select_related('author__profile').order_by('-created_at')[:5]
    
    # Get funeral updates
    updates = FuneralUpdate.objects.filter(
        memorial=memorial
    ).select_related('created_by__profile').order_by('-is_pinned', '-is_urgent', '-created_at')[:3]
    
    # Statistics
    stats = { # type: ignore
        'total_posts': memorial.posts.count(), # type: ignore
        'total_condolences': memorial.condolences.filter(is_approved=True).count(), # type: ignore
        'total_memories': memorial.posts.filter(post_type='memory').count(), # type: ignore
        'days_since_passing': memorial.days_since_passing,
    }
    
    context = {
        'memorial': memorial,
        'posts': posts,
        'condolences': condolences,
        'updates': updates,
        'stats': stats,
        'is_family_admin': memorial.is_admin(request.user) if request.user.is_authenticated else False,
        'can_post': memorial.associated_group.is_member(request.user) if request.user.is_authenticated else False,
    }
    
    return render(request, 'memorial/memorial_detail.html', context)


@login_required
def create_memorial_view(request, group_slug):
    """Create memorial page for a group"""
    group = get_object_or_404(Group, slug=group_slug, is_active=True)
    
    # Check if user is group admin
    if not group.is_admin(request.user):
        messages.error(request, "Only group admins can create memorial pages.")
        return redirect('group_detail', slug=group_slug)
    
    # Check if memorial already exists
    if request.method == 'POST':
        form = MemorialCreationForm(request.POST, request.FILES, group=group)
        if form.is_valid():
            memorial = form.save(commit=False)
            memorial.created_by = request.user
            memorial.associated_group = group

            deceased_user = form.cleaned_data.get('deceased_user')
            if deceased_user:
                # Auto-fill from user profile
                memorial.full_name = deceased_user.get_full_name()
                if hasattr(deceased_user, "date_of_birth"):
                    memorial.date_of_birth = deceased_user.date_of_birth

            memorial.save()
            memorial.family_admins.add(request.user)
            messages.success(request, f"Memorial page created for {memorial.full_name}.")
            return redirect('memorial_detail', pk=memorial.pk)
    else:
        form = MemorialCreationForm(group=group)
    
    return render(request, 'memorial/create_memorial.html', {
        'form': form,
        'group': group,
    })


def memorial_posts_view(request, pk):
    """View all posts for a memorial"""
    memorial = get_object_or_404(Memorial, pk=pk)
    
    # Permission check
    if not memorial.is_public and not request.user.is_authenticated:
        return redirect('login')
    
    # Filter posts
    post_type = request.GET.get('type', '')
    posts = memorial.posts.all() # type: ignore
    
    if post_type:
        posts = posts.filter(post_type=post_type)
    
    # Exclude family-only posts for non-family members
    if not memorial.is_admin(request.user):
        posts = posts.filter(is_family_only=False)
    
    posts = posts.select_related('author__profile').prefetch_related('images', 'likes')
    
    # Pagination
    paginator = Paginator(posts, 15)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    
    context = {
        'memorial': memorial,
        'posts': page_posts,
        'current_filter': post_type,
        'post_types': Post.POST_TYPES,
        'is_family_admin': memorial.is_admin(request.user) if request.user.is_authenticated else False,
    }
    
    return render(request, 'memorial/posts_list.html', context)


@login_required
def create_post_view(request, memorial_pk):
    """Create a new memorial post"""
    memorial = get_object_or_404(Memorial, pk=memorial_pk)
    
    # Check permissions
    if not memorial.associated_group.is_member(request.user):
        messages.error(request, "You must be a group member to post.")
        return redirect('memorial_detail', pk=memorial_pk)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.memorial = memorial
            post.save()
            
            # Handle image uploads
            images = request.FILES.getlist('images')
            for image in images:
                post_image = PostImage.objects.create(
                    image=image,
                    uploaded_by=request.user
                )
                post.images.add(post_image)
            
            messages.success(request, 'Your post has been shared.')
            return redirect('memorial_detail', pk=memorial_pk)
    else:
        form = PostForm()
    
    return render(request, 'memorial/create_post.html', {
        'form': form,
        'memorial': memorial,
    })


def condolences_view(request, memorial_pk):
    """View all condolence messages"""
    memorial = get_object_or_404(Memorial, pk=memorial_pk)
    
    condolences = memorial.condolences.filter( # type: ignore
        is_approved=True
    ).select_related('author__profile').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(condolences, 20)
    page_number = request.GET.get('page')
    page_condolences = paginator.get_page(page_number)
    
    # Condolence form for authenticated users
    condolence_form = None
    if request.user.is_authenticated:
        if request.method == 'POST':
            condolence_form = CondolenceForm(request.POST)
            if condolence_form.is_valid():
                condolence = condolence_form.save(commit=False)
                condolence.memorial = memorial
                condolence.author = request.user
                condolence.save()
                
                messages.success(request, 'Your condolence message has been shared.')
                return redirect('condolences', memorial_pk=memorial_pk)
        else:
            condolence_form = CondolenceForm()
    
    context = {
        'memorial': memorial,
        'condolences': page_condolences,
        'condolence_form': condolence_form,
        'total_condolences': memorial.condolences.filter(is_approved=True).count(), # type: ignore
    }
    
    return render(request, 'memorial/condolences.html', context)


@login_required
def funeral_updates_view(request, memorial_pk):
    """View and manage funeral updates"""
    memorial = get_object_or_404(Memorial, pk=memorial_pk)
    
    updates = memorial.updates.all().select_related('created_by__profile') # type: ignore
    
    # Only family admins can create updates
    update_form = None
    if memorial.is_admin(request.user):
        if request.method == 'POST':
            update_form = FuneralUpdateForm(request.POST)
            if update_form.is_valid():
                update = update_form.save(commit=False)
                update.memorial = memorial
                update.created_by = request.user
                update.save()
                
                messages.success(request, 'Funeral update posted.')
                return redirect('funeral_updates', memorial_pk=memorial_pk)
        else:
            update_form = FuneralUpdateForm()
    
    context = {
        'memorial': memorial,
        'updates': updates,
        'update_form': update_form,
        'is_family_admin': memorial.is_admin(request.user),
    }
    
    return render(request, 'memorial/funeral_updates.html', context)


# AJAX Views for interactivity

@login_required
@require_POST
def toggle_post_like(request, post_pk):
    """Toggle like on a post"""
    post = get_object_or_404(Post, pk=post_pk)
    
    like, created = PostLike.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    # Update count is handled by signals
    return JsonResponse({
        'liked': liked,
        'likes_count': post.likes_count
    })


@login_required
@require_POST
def add_comment(request, post_pk):
    """Add comment to a post"""
    post = get_object_or_404(Post, pk=post_pk)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')
        
        if not content:
            return JsonResponse({'error': 'Comment cannot be empty'}, status=400)
        
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content,
            parent_id=parent_id if parent_id else None
        )
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': str(comment.id),
                'content': comment.content,
                'author_name': comment.author.profile.full_name or comment.author.email,
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'likes_count': 0,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def edit_post_view(request, post_pk):
    """Edit a memorial post"""
    post = get_object_or_404(Post, pk=post_pk)
    
    # Check permissions
    if not post.can_edit(request.user):
        messages.error(request, "You don't have permission to edit this post.")
        return redirect('memorial_detail', pk=post.memorial.pk)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully.')
            return redirect('memorial_detail', pk=post.memorial.pk)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'memorial/edit_post.html', {
        'form': form,
        'post': post,
        'memorial': post.memorial,
    })


@login_required
@require_POST
def delete_post_view(request, post_pk):
    """Delete a memorial post"""
    post = get_object_or_404(Post, pk=post_pk)
    memorial_pk = post.memorial.pk
    
    if post.can_delete(request.user):
        post.delete()
        messages.success(request, 'Post deleted successfully.')
    else:
        messages.error(request, "You don't have permission to delete this post.")
    
    return redirect('memorial_detail', pk=memorial_pk)


@login_required
def memorial_manage_view(request, memorial_pk):
    """Memorial management dashboard for family admins"""
    memorial = get_object_or_404(Memorial, pk=memorial_pk)
    
    if not memorial.is_admin(request.user):
        messages.error(request, "You don't have permission to manage this memorial.")
        return redirect('memorial_detail', pk=memorial_pk)
    
    # Recent activity
    recent_posts = memorial.posts.select_related('author__profile').order_by('-created_at')[:5] # type: ignore
    pending_condolences = memorial.condolences.filter(is_approved=False).order_by('-created_at')[:5] # type: ignore
    
    # Statistics
    stats = {
        'total_posts': memorial.posts.count(), # type: ignore
        'total_condolences': memorial.condolences.count(), # type: ignore
        'pending_condolences': memorial.condolences.filter(is_approved=False).count(), # type: ignore
        'total_comments': Comment.objects.filter(post__memorial=memorial).count(),
        'recent_activity': memorial.posts.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7)).count(), # type: ignore
    }
    
    context = {
        'memorial': memorial,
        'recent_posts': recent_posts,
        'pending_condolences': pending_condolences,
        'stats': stats,
    }
    
    return render(request, 'memorial/manage_memorial.html', context)