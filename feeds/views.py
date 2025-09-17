# feeds/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Exists, OuterRef
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.db.models.signals import m2m_changed
from datetime import timedelta, datetime
import json
from notifications.models import Notification
from notifications.utils import NotificationService
from .models import (
    Feed, Post, PostMedia, Comment, PostLike, CommentLike, 
    PostShare, Poll, PollOption, PollVote, FeedActivity
)
from group.models import Group
from memorial.models import Memorial


@login_required
def group_feed_view(request, slug):
    """Main feed view - adapts to any group type"""
    group = get_object_or_404(Group, slug=slug)

    # Check permissions
    if not group.is_member(request.user) and not group.is_public: # type: ignore
        messages.error(request, "You need to join this group to view its feed.")
        return redirect('group:group_detail', slug=slug)

    # Get or create feed for the group
    feed, created = Feed.objects.get_or_create(group=group)
    
    # Get filter from query params
    post_filter = request.GET.get('filter', 'all')
    
    # Build posts query
    posts_query = Post.objects.filter(
        feed=feed,
        is_approved=True
    ).select_related(
        'author__profile',
        'memorial_related',
        'poll'
    ).prefetch_related(
        'media',
        'likes',
        'comments__author__profile',
        'poll__options__votes'
    )
    
    # Apply filters
    if post_filter != 'all':
        posts_query = posts_query.filter(post_type=post_filter)
    
    # Check if user can view based on privacy levels
    if request.user.is_authenticated:
        # Get posts user can view based on privacy
        posts_query = posts_query.filter(
            Q(privacy_level='public') |
            Q(privacy_level='members_only', feed__group__memberships__user=request.user, feed__group__memberships__status='active') |
            Q(privacy_level='admins_only', feed__group__admins=request.user) |
            Q(author=request.user)
        ).distinct()
    else:
        posts_query = posts_query.filter(privacy_level='public')
    
    # Ordering with engagement scoring
    posts_query = posts_query.order_by('-is_pinned', '-is_urgent', '-created_at')
    
    # Pagination
    paginator = Paginator(posts_query, 10)
    page_number = request.GET.get('page', 1)
    posts = paginator.get_page(page_number)

    # Add can_edit attribute for each post
    for post in posts:
        post.user_can_edit = post.can_edit(request.user)
    
    # Get online members (last 15 minutes)
    online_threshold = timezone.now() - timedelta(minutes=15)
    online_members = group.members.filter(
        last_login__gte=online_threshold
    )[:10]
    
    # Context data
    context = {
        'group': group,
        'feed': feed,
        'posts': posts,
        'online_members': online_members,
        'can_post': group.is_member(request.user) if request.user.is_authenticated else False,
        'is_admin': group.is_admin(request.user) if request.user.is_authenticated else False,
        'current_filter': post_filter,
        
        # Stats for sidebar
        'stats': {
            'total_posts': feed.posts.filter(is_approved=True).count(), # type: ignore
            'posts_today': feed.posts.filter( # type: ignore
                is_approved=True,
                created_at__date=timezone.now().date()
            ).count(),
            'active_members': online_members.count(),
        }
    }
    
    # Track page view activity
    if request.user.is_authenticated:
        FeedActivity.objects.create(
            user=request.user,
            post=None,  # General feed view
            activity_type='view',
            metadata={'page': page_number, 'filter': post_filter}
        )
    
    return render(request, 'feeds/social_feed.html', context)

#----------------------------------create_post_view------------------------------------------------#

@login_required
def create_post_view(request, group_pk):
    """Create a new post - universal for all group types"""
    group = get_object_or_404(Group, pk=group_pk)
    feed  = get_object_or_404(Feed, group=group)
    
    # Check permissions
    if not group.is_member(request.user):
        messages.error(request, "You must be a group member to create posts.")
        return redirect('feeds:group_feed', slug=group.slug)
    
    if not feed.allow_posts:
        messages.error(request, "Posting is disabled for this group.")
        return redirect('feeds:group_feed', slug=group.slug)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create post
                post = Post.objects.create(
                    author=request.user,
                    feed=feed,
                    post_type=request.POST.get('post_type', 'text'),
                    title=request.POST.get('title', '').strip(),
                    content=request.POST.get('content', '').strip(),
                    link_url=request.POST.get('link_url', '').strip(),
                    location=request.POST.get('location', '').strip(),
                    is_anonymous=request.POST.get('is_anonymous') == 'on',
                    privacy_level=request.POST.get('privacy_level', 'public'),
                    is_approved=not feed.require_approval
                )
                
                # Handle memorial relation
                if request.POST.get('memorial_related'):
                    try:
                        memorial = Memorial.objects.get(
                            pk=request.POST['memorial_related'],
                            associated_group=group
                        )
                        post.memorial_related = memorial # type: ignore
                        post.save()
                    except Memorial.DoesNotExist:
                        pass
                
                # Handle event dates
                if post.post_type == 'event':
                    event_date = request.POST.get('event_date')
                    if event_date:
                        post.event_date = event_date
                        post.save()
                
                # Handle media uploads
                media_files = request.FILES.getlist('media_files')
                for media_file in media_files:
                    # Determine media type
                    if media_file.content_type.startswith('image/'):
                        media_type = 'image'
                    elif media_file.content_type.startswith('video/'):
                        media_type = 'video'
                    elif media_file.content_type.startswith('audio/'):
                        media_type = 'audio'
                    else:
                        media_type = 'document'
                    
                    PostMedia.objects.create(
                        post=post,
                        media_type=media_type,
                        file=media_file,
                        caption=request.POST.get(f'caption_{media_file.name}', ''),
                        uploaded_by=request.user
                    )
                
                # Handle poll creation
                if post.post_type == 'poll':
                    poll_question = request.POST.get('poll_question', '').strip()
                    if poll_question:
                        poll = Poll.objects.create(
                            post=post,
                            question=poll_question,
                            is_multiple_choice=request.POST.get('poll_multiple') == 'on'
                        )
                        
                        # Create poll options
                        for i in range(1, 11):  # Max 10 options
                            option_text = request.POST.get(f'poll_option_{i}', '').strip()
                            if option_text:
                                PollOption.objects.create(
                                    poll=poll,
                                    text=option_text
                                )
                
                messages.success(
                    request, 
                    'Your post has been shared!' if post.is_approved 
                    else 'Your post is pending approval.'
                )
                
                return redirect('feeds:group_feed', slug=group.slug)
                
        except Exception as e:
            messages.error(request, f'Error creating post: {str(e)}')
            return redirect('feeds:group_feed', slug=group.slug)
    
    # GET request - show form
    context = {
        'group': group,
        'feed': feed,
        'post_types': Post.POST_TYPES,
        'privacy_levels': Post.PRIVACY_LEVELS,
        'memorial': getattr(group, 'memorial', None),
    }
    return render(request, 'feeds/create_post.html', context)

#--------------------------------post_detail_view------------------------------------------------#

@login_required
def post_detail_view(request, pk):
    """Detailed view of a single post"""
    post = get_object_or_404(
        Post.objects.select_related(
            'author__profile',
            'feed__group',
            'memorial_related',
            'poll'
        ).prefetch_related(
            'media',
            'likes__user',
            'comments__author__profile',
            'comments__replies__author__profile',
            'poll__options__votes'
        ), 
        pk=pk
    )
    
    # Check permissions
    if not post.can_view(request.user):
        raise Http404("Post not found or you don't have permission to view it.")
    
    # Get comments with replies
    comments = post.comments.filter( # type: ignore
        parent=None  # Top-level comments only
    ).order_by('-created_at')
    
    # Track view activity
    if request.user.is_authenticated:
        FeedActivity.objects.get_or_create(
            user=request.user,
            post=post,
            activity_type='view',
            defaults={'metadata': {}}
        )
        
        # Increment view count
        post.views_count += 1
        post.save(update_fields=['views_count'])
    
    context = {
        'post': post,
        'comments': comments,
        'can_edit': post.can_edit(request.user),
        'can_comment': post.feed.group.is_member(request.user) if request.user.is_authenticated else False,
        'user_liked': post.likes.filter(user=request.user).exists() if request.user.is_authenticated else False, # type: ignore
    }
    
    return render(request, 'feeds/post_detail.html', context)

#-----------------------------------toggle_post_like---------------------------------------------#

@login_required
@require_http_methods(["POST"])
def toggle_post_like(request, pk):
    """Toggle like/unlike on a post"""
    post = get_object_or_404(Post, pk=pk)
    
    if not post.can_view(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    like, created = PostLike.objects.get_or_create(
        user=request.user,
        post=post,
        defaults={'reaction_type': request.POST.get('reaction_type', 'like')}
    )
    
    if not created:
        # Already liked, remove like
        like.delete()
        liked = False
    else:
        # Track like activity
        FeedActivity.objects.create(
            user=request.user,
            post=post,
            activity_type='like',
            metadata={'reaction_type': like.reaction_type}
        )
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'count': post.likes_count,
        'reaction_type': like.reaction_type if liked else None
    })

#-----------------------------------add_comment---------------------------------------------#

@login_required
@require_http_methods(["POST"])
def add_comment(request, pk):
    """Add a comment to a post"""
    post = get_object_or_404(Post, pk=pk)
    
    if not post.feed.group.is_member(request.user):
        return JsonResponse({'error': 'Must be a group member to comment'}, status=403)
    
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')
    
    if not content:
        return JsonResponse({'error': 'Comment content required'}, status=400)
    
    parent = None
    if parent_id:
        try:
            parent = Comment.objects.get(id=parent_id, post=post)
        except Comment.DoesNotExist:
            return JsonResponse({'error': 'Parent comment not found'}, status=404)
    
    comment = Comment.objects.create(
        post=post,
        author=request.user,
        content=content,
        parent=parent,
        is_anonymous=request.POST.get('is_anonymous') == 'true'
    )
    
    # Track comment activity
    FeedActivity.objects.create(
        user=request.user,
        post=post,
        activity_type='comment',
        metadata={'comment_id': str(comment.pk)}
    )
    
    return JsonResponse({
        'success': True,
        'post_id': post.pk,
        'comment_id': str(comment.pk),
        'author_name': 'Anonymous' if comment.is_anonymous else (
            comment.author.profile.full_name if hasattr(comment.author, 'profile') 
            else comment.author.email
        ),
        'author_avatar': comment.author.profile.profile_picture.url if hasattr(comment.author, 'profile') and comment.author.profile.profile_picture else '/static/images/default_avatar.png',
        'content': comment.content,
        'created_at': comment.created_at.isoformat(),
        'can_edit': comment.can_edit(request.user)
    })

#-------------------share_post-----------------------------------------------------------#

@login_required
@require_http_methods(["POST"])
def share_post(request, pk):
    """Share a post to another group or user's timeline"""
    post = get_object_or_404(Post, pk=pk)
    
    if not post.can_view(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    target_feed_id = request.POST.get('target_feed_id')
    message = request.POST.get('message', '').strip()
    
    target_feed = None
    if target_feed_id:
        try:
            target_feed = Feed.objects.get(pk=target_feed_id)
            if not target_feed.group.is_member(request.user):
                return JsonResponse({'error': 'Cannot share to that group'}, status=403)
        except Feed.DoesNotExist:
            return JsonResponse({'error': 'Target feed not found'}, status=404)
    
    share, created = PostShare.objects.get_or_create(
        user=request.user,
        post=post,
        shared_to_feed=target_feed,
        defaults={'message': message}
    )
    
    if created:
        # Track share activity
        FeedActivity.objects.create(
            user=request.user,
            post=post,
            activity_type='share',
            metadata={'target_feed_id': str(target_feed.pk) if target_feed else None}
        )
    
    return JsonResponse({
        'success': True,
        'shared': created,
        'share_count': post.shares_count
    })

#-----------------------------------vote_poll---------------------------------------------#

@login_required
@require_http_methods(["POST"])
def vote_poll(request, option_pk):
    """Vote in a poll"""
    option = get_object_or_404(PollOption, pk=option_pk)
    post = option.poll.post
    
    if not post.can_view(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if option.poll.is_expired:
        return JsonResponse({'error': 'Poll has expired'}, status=400)
    
    # Check if user already voted
    existing_votes = PollVote.objects.filter(
        user=request.user,
        option__poll=option.poll
    )
    
    if existing_votes.exists() and not option.poll.is_multiple_choice:
        # Remove existing vote if single choice
        existing_votes.delete()
    
    vote, created = PollVote.objects.get_or_create(
        user=request.user,
        option=option,
        defaults={'other_text': request.POST.get('other_text', '')}
    )
    
    if not created:
        # Already voted, remove vote
        vote.delete()
        voted = False
    else:
        # Track vote activity
        FeedActivity.objects.create(
            user=request.user,
            post=post,
            activity_type='vote_poll',
            metadata={'option_id': str(option.pk)}
        )
        voted = True
    
    # Calculate updated percentages
    total_votes = option.poll.total_votes
    options_data = []
    
    for poll_option in option.poll.options.all(): # type: ignore
        percentage = (poll_option.votes_count * 100 // total_votes) if total_votes > 0 else 0
        options_data.append({
            'id': str(poll_option.pk),
            'text': poll_option.text,
            'votes': poll_option.votes_count,
            'percentage': percentage,
            'voted': PollVote.objects.filter(user=request.user, option=poll_option).exists()
        })
    
    return JsonResponse({
        'success': True,
        'voted': voted,
        'total_votes': total_votes,
        'options': options_data
    })

#-----------------------------------edit_post_view---------------------------------------------#

@login_required
def edit_post_view(request, pk):
    """Edit an existing post"""
    post = get_object_or_404(Post, pk=pk)
    
    if not post.can_edit(request.user):
        messages.error(request, "You don't have permission to edit this post.")
        return redirect('feeds:post_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update basic fields
                post.title = request.POST.get('title', '').strip()
                post.content = request.POST.get('content', '').strip()
                post.link_url = request.POST.get('link_url', '').strip()
                post.location = request.POST.get('location', '').strip()
                post.privacy_level = request.POST.get('privacy_level', post.privacy_level)
                
                # Only allow post type change for certain types
                if post.post_type in ['text', 'photo', 'link']:
                    new_type = request.POST.get('post_type')
                    if new_type in ['text', 'photo', 'link']:
                        post.post_type = new_type
                
                post.save()
                
                # Handle new media uploads
                media_files = request.FILES.getlist('new_media_files')
                for media_file in media_files:
                    if media_file.content_type.startswith('image/'):
                        media_type = 'image'
                    elif media_file.content_type.startswith('video/'):
                        media_type = 'video'
                    else:
                        media_type = 'document'
                    
                    PostMedia.objects.create(
                        post=post,
                        media_type=media_type,
                        file=media_file,
                        uploaded_by=request.user
                    )
                
                # Handle media deletions
                media_to_delete = request.POST.getlist('delete_media')
                if media_to_delete:
                    PostMedia.objects.filter(
                        post=post,
                        pk__in=media_to_delete
                    ).delete()
                
                messages.success(request, 'Post updated successfully!')
                return redirect('feeds:post_detail', pk=pk)
                
        except Exception as e:
            messages.error(request, f'Error updating post: {str(e)}')
    
    context = {
        'post': post,
        'privacy_levels': Post.PRIVACY_LEVELS,
    }
    
    return render(request, 'feeds/edit_post.html', context)


@login_required
@require_http_methods(["POST"])
def delete_post(request, pk):
    """Delete a post"""
    post = get_object_or_404(Post, pk=pk)
    
    if not post.can_delete(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    group_slug = post.feed.group.slug
    post.delete()
    
    messages.success(request, 'Post deleted successfully.')
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({'success': True, 'redirect': f'/groups/{group_slug}/feed/'})
    else:
        return redirect('feeds:group_feed', slug=group_slug)


def posts_api_view(request, group_pk):
    """API endpoint for loading more posts (AJAX)"""
    group = get_object_or_404(Group, pk=group_pk)
    
    if not group.is_member(request.user) and not group.is_public: # type: ignore
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    page = int(request.GET.get('page', 1))
    post_filter = request.GET.get('filter', 'all')
    
    # Build query same as main feed
    posts_query = Post.objects.filter(
        feed__group=group,
        is_approved=True
    ).select_related('author__profile')
    
    if post_filter != 'all':
        posts_query = posts_query.filter(post_type=post_filter)
    
    # Apply privacy filters
    if request.user.is_authenticated:
        posts_query = posts_query.filter(
            Q(privacy_level='public') |
            Q(privacy_level='members_only', feed__group__memberships__user=request.user, feed__group__memberships__status='active') |
            Q(author=request.user)
        ).distinct()
    else:
        posts_query = posts_query.filter(privacy_level='public')
    
    paginator = Paginator(posts_query.order_by('-is_pinned', '-created_at'), 10)
    posts = paginator.get_page(page)
    
    posts_data = []
    for post in posts:
        posts_data.append({
            'id': str(post.pk),
            'title': post.title,
            'content': post.content,
            'author': post.author.profile.full_name if hasattr(post.author, 'profile') else post.author.email,
            'created_at': post.created_at.isoformat(),
            'post_type': post.post_type,
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
            'url': post.get_absolute_url(),
        })
    
    return JsonResponse({
        'posts': posts_data,
        'has_next': posts.has_next(),
        'next_page': posts.next_page_number() if posts.has_next() else None
    })


@login_required
def group_posts_view(request, group_pk):
    """View all posts for a group (paginated list)"""
    group = get_object_or_404(Group, pk=group_pk)
    
    if not group.is_member(request.user) and not group.is_public: # type: ignore
        messages.error(request, "You need to join this group to view its posts.")
        return redirect('group:group_detail', slug=group.slug)
    
    posts = Post.objects.filter(
        feed__group=group,
        is_approved=True
    ).select_related(
        'author__profile'
    ).prefetch_related(
        'media'
    ).order_by('-is_pinned', '-created_at')
    
    # Filter by type if specified
    post_type = request.GET.get('type')
    if post_type:
        posts = posts.filter(post_type=post_type)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    
    context = {
        'group': group,
        'posts': page_posts,
        'search_query': search_query,
        'current_type': post_type,
        'post_types': Post.POST_TYPES,
    }
    
    return render(request, 'feeds/posts_list.html', context)


# Memorial Integration Views

@login_required
def memorial_feed_integration(request, memorial_pk):
    """Show memorial-related posts in the group feed"""
    memorial = get_object_or_404(Memorial, pk=memorial_pk)
    
    if not memorial.associated_group.is_member(request.user):
        messages.error(request, "You must be a group member to view memorial posts.")
        return redirect('group:group_detail', slug=memorial.associated_group.slug)
    
    # Get all memorial-related posts
    memorial_posts = Post.objects.filter(
        memorial_related=memorial,
        is_approved=True
    ).select_related(
        'author__profile'
    ).prefetch_related(
        'media', 'likes', 'comments'
    ).order_by('-is_pinned', '-created_at')
    
    paginator = Paginator(memorial_posts, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'memorial': memorial,
        'group': memorial.associated_group,
        'posts': posts,
        'can_post': True,  # Members can always post memorial content
    }
    
    return render(request, 'feeds/memorial_feed.html', context)



@login_required
@require_http_methods(["POST"])
def enhanced_toggle_post_like(request, pk):
    """Enhanced like function with notification integration"""
    post = get_object_or_404(Post, pk=pk)
    
    if not post.can_view(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    reaction_type = request.POST.get('reaction_type', 'like')
    
    like, created = PostLike.objects.get_or_create(
        user=request.user,
        post=post,
        defaults={'reaction_type': reaction_type}
    )
    
    if not created:
        # Update reaction type or remove if same
        if like.reaction_type == reaction_type:
            like.delete()
            liked = False
        else:
            like.reaction_type = reaction_type
            like.save()
            liked = True
    else:
        liked = True
        
        # Create activity tracking
        from .models import FeedActivity
        FeedActivity.objects.create(
            user=request.user,
            post=post,
            activity_type='like',
            metadata={'reaction_type': reaction_type}
        )
    
    # Get reaction counts
    reaction_counts = {}
    for reaction in ['like', 'love', 'care', 'support']:
        count = PostLike.objects.filter(post=post, reaction_type=reaction).count()
        if count > 0:
            reaction_counts[reaction] = count
    
    return JsonResponse({
        'liked': liked,
        'reaction_type': reaction_type,
        'total_likes': post.likes_count,
        'reaction_counts': reaction_counts,
        'user_reaction': reaction_type if liked else None
    })


@login_required
def hub_integrated_feed_view(request, slug):
    """Feed view with hub integration data"""
    group = get_object_or_404(Group, slug=slug)
    
    # Your existing feed logic here...
    feed, created = Feed.objects.get_or_create(group=group)
    
    # Get posts with enhanced data for hub
    posts_query = Post.objects.filter(
        feed=feed,
        is_approved=True
    ).select_related(
        'author__profile',
        'memorial_related',
        'poll'
    ).prefetch_related(
        'media',
        'likes',
        'comments__author__profile'
    )
    
    # Apply privacy filters (your existing logic)
    if request.user.is_authenticated:
        posts_query = posts_query.filter(
            Q(privacy_level='public') |
            Q(privacy_level='members_only', feed__group__memberships__user=request.user) |
            Q(author=request.user)
        ).distinct()
    
    posts_query = posts_query.order_by('-is_pinned', '-is_urgent', '-created_at')
    
    # Pagination
    paginator = Paginator(posts_query, 10)
    page_number = request.GET.get('page', 1)
    posts = paginator.get_page(page_number)
    
    # Enhanced context with hub integration
    context = {
        'group': group,
        'feed': feed,
        'posts': posts,
        'can_post': group.is_member(request.user) if request.user.is_authenticated else False,
        
        # Hub integration data
        'recent_notifications': get_group_notifications(request.user, group) if request.user.is_authenticated else [],
        'group_stats': get_enhanced_group_stats(group),
        'quick_actions': get_hub_quick_actions(group, request.user),
        
        # Feed-specific stats
        'feed_stats': {
            'posts_today': posts_query.filter(created_at__date=timezone.now().date()).count(),
            'total_posts': posts_query.count(),
            'total_comments': Comment.objects.filter(post__feed=feed).count(),
            'total_likes': PostLike.objects.filter(post__feed=feed).count(),
        }
    }
    
    return render(request, 'feeds/hub_integrated_feed.html', context)


def get_group_notifications(user, group):
    """Get recent group-specific notifications"""
    return Notification.objects.filter(
        recipient=user,
        data__group_id=group.id
    ).order_by('-created_at')[:5]


def get_enhanced_group_stats(group):
    """Get comprehensive group statistics"""
    from datetime import timedelta
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    return {
        'total_members': group.members.count(),
        'total_posts': Post.objects.filter(feed__group=group, is_approved=True).count(),
        'posts_this_week': Post.objects.filter(
            feed__group=group, 
            is_approved=True,
            created_at__date__gte=week_ago
        ).count(),
        'total_comments': Comment.objects.filter(post__feed__group=group).count(),
        'total_likes': PostLike.objects.filter(post__feed__group=group).count(),
        'active_polls': Poll.objects.filter(
            post__feed__group=group,
            expires_at__gt=timezone.now()
        ).count(),
    }


def get_hub_quick_actions(group, user):
    """Get available quick actions for the hub"""
    actions = []
    
    if user.is_authenticated and group.is_member(user):
        actions.extend([
            {
                'name': 'Create Post',
                'icon': 'bi-plus-circle',
                'url': f'/groups/{group.id}/feed/create-post/',
                'color': 'primary'
            },
            {
                'name': 'View Photos',
                'icon': 'bi-images',
                'url': f'/groups/{group.id}/feed/?filter=photo',
                'color': 'success'
            },
            {
                'name': 'Upcoming Events',
                'icon': 'bi-calendar',
                'url': f'/groups/{group.id}/feed/?filter=event',
                'color': 'info'
            }
        ])
        
        if hasattr(group, 'memorial'):
            actions.append({
                'name': 'Share Memory',
                'icon': 'bi-heart',
                'url': f'/groups/{group.id}/feed/create-post/?type=memory',
                'color': 'danger'
            })
    
    return actions


# API endpoint for real-time feed updates
@login_required
def feed_updates_api(request, group_pk):
    """API endpoint for real-time feed updates"""
    group = get_object_or_404(Group, pk=group_pk)
    
    if not group.is_member(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    last_check = request.GET.get('since')
    if last_check:
        try:
            from datetime import datetime
            last_check_time = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
            
            new_posts = Post.objects.filter(
                feed__group=group,
                is_approved=True,
                created_at__gt=last_check_time
            ).count()
            
            new_comments = Comment.objects.filter(
                post__feed__group=group,
                created_at__gt=last_check_time
            ).exclude(author=request.user).count()
            
            new_notifications = Notification.objects.filter(
                recipient=request.user,
                data__group_id=group.id,
                created_at__gt=last_check_time,
                read_at__isnull=True
            ).count()
            
            return JsonResponse({
                'has_updates': new_posts > 0 or new_comments > 0 or new_notifications > 0,
                'new_posts': new_posts,
                'new_comments': new_comments,
                'new_notifications': new_notifications,
                'timestamp': timezone.now().isoformat()
            })
            
        except ValueError:
            pass
    
    return JsonResponse({'has_updates': False})


# Batch notification handler for multiple likes
from django.dispatch import receiver
def batch_like_notification(sender, instance, action, pk_set, **kwargs):
    """Handle batch notifications for multiple likes"""
    if action != 'post_add':
        return
    
    post = instance
    
    # Only send batch notification if post has multiple likes and author isn't among the likers
    if post.likes_count >= 3:
        # Get recent notifications for this post to avoid spam
        recent_notifications = Notification.objects.filter(
            recipient=post.author,
            related_object_id=post.id,
            notification_type='group_updated',
            created_at__gte=timezone.now() - timedelta(hours=1)
        )
        
        if not recent_notifications.exists():
            # Create a summary notification
            likers = post.likes.exclude(user=post.author).select_related('user')[:3]
            liker_names = [like.user.get_full_name() or like.user.username for like in likers]
            
            if post.likes_count > 3:
                message = f"{', '.join(liker_names)} and {post.likes_count - 3} others reacted to your post"
            else:
                message = f"{', '.join(liker_names)} reacted to your post"
            
            NotificationService.create_notification(
                recipient=post.author,
                notification_type='group_updated',
                title=f"{post.likes_count} reactions on your post",
                message=message,
                related_object=post,
                action_url=post.get_absolute_url(),
                priority='low',
                data={
                    'group_id': post.feed.group.id,
                    'post_id': post.id,
                    'total_likes': post.likes_count,
                    'is_batch_notification': True
                }
            )