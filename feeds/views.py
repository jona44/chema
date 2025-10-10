from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F, Prefetch
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime
from .models import Feed, Post, Comment, PostLike, CommentLike, FeedActivity, PostMedia
from group.models import Group
from .models import Feed, Post, PostMedia
from group.models import Group
from .utils import process_media_file, validate_media_file


@login_required
def group_feed_view(request, slug):
    """Main group feed view"""
    group = get_object_or_404(Group, slug=slug)
    
    # Check if user can access this group
    if not group.is_member(request.user) and not (group.privacy == 'public'):
        messages.error(request, "You don't have access to this group.")
        return redirect('group_list')
    
    # Use get_or_create to ensure a feed always exists for a group.
    # This prevents a 404 error if a group is created without a corresponding feed.
    feed, created = Feed.objects.get_or_create(group=group)

    # If the feed was just created and has no posts, add a default welcome post.
    if created and group.creator and not Post.objects.filter(feed=feed).exists():
        Post.objects.create(
            author=group.creator,
            feed=feed,
            title=f"Welcome to {group.name}!",
            content="This is the beginning of your group's feed. Start by sharing a post!",
            post_type='announcement',
            is_pinned=True,
            is_approved=True
        )
    
    # Get posts with filtering
    posts_queryset = Post.objects.filter(
        feed=feed,
        is_approved=True
    ).select_related('author', 'author__profile').prefetch_related(
        'media', 'likes', 'comments__author'
    )
    
    # Apply privacy filtering
    if not request.user.is_authenticated:
        posts_queryset = posts_queryset.filter(privacy_level='public')
    elif not group.is_member(request.user):
        posts_queryset = posts_queryset.filter(privacy_level='public')
    
    # Pagination
    paginator = Paginator(posts_queryset, 10)
    page_number = request.GET.get('page', 1)
    posts = paginator.get_page(page_number)
    
        # Set can_edit attribute for each post
    for post in posts.object_list:
        post.can_edit = post.can_edit(request.user)
    # Get recent activities for sidebar
    recent_activities = FeedActivity.objects.filter(
        post__feed=feed
    ).select_related('user', 'post').order_by('-created_at')[:5]
    
    context = {
        'group': group,
        'feed': feed,
        'posts': posts,
        'recent_activities': recent_activities,
        'can_post': feed.allow_posts and group.is_member(request.user),
        'is_admin': group.is_admin(request.user),
    }
    
    return render(request, 'feeds/group_feed.html', context)


@login_required
@require_http_methods(["POST"])
def create_post_view(request, group_slug):
    """Create a new post via HTMX"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    if not feed.allow_posts or not group.is_member(request.user):
        response = JsonResponse({'error': 'Not allowed to post'}, status=403)
        response['HX-Reswap'] = 'none'  # Don't swap content on error
        return response
    
    content = request.POST.get('content', '').strip()
    post_type = request.POST.get('post_type', 'text')
    privacy_level = request.POST.get('privacy_level', 'public')
    title = request.POST.get('title', '').strip()
    is_urgent = request.POST.get('is_urgent') == 'on'
    is_anonymous = request.POST.get('is_anonymous') == 'on'
    
    if not content:
        response = JsonResponse({'error': 'Content is required'}, status=400)
        response['HX-Reswap'] = 'none'  # Don't swap content on error
        return response
    
    try:
        # Create the post
        post = Post.objects.create(
            author=request.user,
            feed=feed,
            content=content,
            title=title if title else None,
            post_type=post_type,
            privacy_level=privacy_level,
            is_urgent=is_urgent,
            is_anonymous=is_anonymous,
            is_approved=not feed.require_approval
        )
        
        # Log activity
        FeedActivity.objects.create(
            user=request.user,
            post=post,
            activity_type='create'
        )
        
        # Render the post partial for HTMX
        html = render_to_string('feeds/partials/post_item.html', {
            'post': post,
            'user': request.user,
            'group': group,
            'feed': feed,
        }, request=request)
        
        # Create response with success headers
        response = HttpResponse(html)
        
        # Add HTMX headers to indicate success and trigger modal close
        response['HX-Trigger'] = 'postCreated'  # Custom event we can listen for
        response['HX-Trigger-After-Swap'] = 'closeModal'  # Close modal after swap
        
        # Add success message
        messages.success(request, 'Post created successfully!')
        
        return response
        
    except Exception as e:
        # Handle any creation errors
        response = JsonResponse({'error': 'Failed to create post'}, status=500)
        response['HX-Reswap'] = 'none'
        return response
    
@login_required
@require_http_methods(["POST"])
def create_media_post_view(request, group_slug):
    """Create a new media post (photo/video) via HTMX"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    # Check permissions
    if not feed.allow_posts or not feed.allow_media or not group.is_member(request.user):
        response = JsonResponse({'error': 'Not allowed to post media'}, status=403)
        response['HX-Reswap'] = 'none'
        return response
    
    # Get form data
    content = request.POST.get('content', '').strip()
    post_type = request.POST.get('post_type', 'photo')  # photo or video
    privacy_level = request.POST.get('privacy_level', 'public')
    title = request.POST.get('title', '').strip()
    is_urgent = request.POST.get('is_urgent') == 'on'
    is_anonymous = request.POST.get('is_anonymous') == 'on'
    
    # Get uploaded files
    media_files = request.FILES.getlist('media_files')
    captions = request.POST.getlist('captions[]')
    alt_texts = request.POST.getlist('alt_texts[]')
    
    # Validation
    if not media_files:
        response = JsonResponse({'error': 'At least one media file is required'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    # Validate media files
    for media_file in media_files:
        if not validate_media_file(media_file, post_type):
            response = JsonResponse({'error': f'Invalid {post_type} file: {media_file.name}'}, status=400)
            response['HX-Reswap'] = 'none'
            return response
    
    try:
        # Create the post
        post = Post.objects.create(
            author=request.user,
            feed=feed,
            content=content,
            title=title if title else None,
            post_type=post_type,
            privacy_level=privacy_level,
            is_urgent=is_urgent,
            is_anonymous=is_anonymous,
            is_approved=not feed.require_approval
        )
        
        # Process and save media files
        for i, media_file in enumerate(media_files):
            caption = captions[i] if i < len(captions) else ''
            alt_text = alt_texts[i] if i < len(alt_texts) else ''
            
            # Process the media file (resize images, generate thumbnails, etc.)
            processed_file, thumbnail, metadata = process_media_file(media_file, post_type)
            
            PostMedia.objects.create(
                post=post,
                media_type='image' if post_type == 'photo' else 'video',
                file=processed_file,
                thumbnail=thumbnail,
                caption=caption,
                alt_text=alt_text,
                file_size=metadata.get('file_size', 0),
                duration=metadata.get('duration'),
                uploaded_by=request.user
            )
        
        # Render the post partial for HTMX
        html = render_to_string('feeds/partials/post_item.html', {
            'post': post,
            'user': request.user,
            'group': group,
            'feed': feed,
        }, request=request)
        
        # Create response with success headers
        response = HttpResponse(html)
        response['HX-Trigger'] = 'postCreated,closeModal'
        
        messages.success(request, f'{post_type.title()} post created successfully!')
        return response
        
    except Exception as e:
        response = JsonResponse({'error': f'Failed to create media post: {str(e)}'}, status=500)
        response['HX-Reswap'] = 'none'
        return response  

    #-------------------- Create the announcement post----------------#
    
@login_required
@require_http_methods(["POST"])
def create_announcement_view(request, group_slug):
    """Create a new announcement post via HTMX"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    # Check permissions - only admins can create announcements
    if not feed.allow_posts or not group.is_admin(request.user):
        response = JsonResponse({'error': 'Only group admins can create announcements'}, status=403)
        response['HX-Reswap'] = 'none'
        return response
    
    # Get form data
    content = request.POST.get('content', '').strip()
    title = request.POST.get('title', '').strip()
    privacy_level = request.POST.get('privacy_level', 'public')
    is_urgent = request.POST.get('is_urgent') == 'on'
    is_pinned = request.POST.get('is_pinned') == 'on'
    
    # Validation
    if not content or not title:
        response = JsonResponse({'error': 'Title and content are required for announcements'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    try:
        # Create the announcement post
        post = Post.objects.create(
            author=request.user,
            feed=feed,
            content=content,
            title=title,
            post_type='announcement',
            privacy_level=privacy_level,
            is_urgent=is_urgent,
            is_pinned=is_pinned,  # Announcements can be pinned
            is_approved=True  # Admin posts are auto-approved
        )
        
        # Render the post partial for HTMX
        html = render_to_string('feeds/partials/post_item.html', {
            'post': post,
            'user': request.user,
            'group': group,
            'feed': feed,
        }, request=request)
        
        # Create response with success headers
        response = HttpResponse(html)
        response['HX-Trigger'] = 'postCreated,closeModal'
        
        messages.success(request, 'Announcement created successfully!')
        return response
        
    except Exception as e:
        response = JsonResponse({'error': f'Failed to create announcement: {str(e)}'}, status=500)
        response['HX-Reswap'] = 'none'
        return response   


@login_required
@require_http_methods(["POST"])
def create_event_post_view(request, group_slug):
    """Create a new event post via HTMX"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    # Check permissions
    if not feed.allow_posts or not feed.allow_events or not group.is_member(request.user):
        response = JsonResponse({'error': 'Not allowed to create events'}, status=403)
        response['HX-Reswap'] = 'none'
        return response
    
    # Get form data
    content = request.POST.get('content', '').strip()
    title = request.POST.get('title', '').strip()
    location = request.POST.get('location', '').strip()
    privacy_level = request.POST.get('privacy_level', 'public')
    is_urgent = request.POST.get('is_urgent') == 'on'
    
    # Event specific fields
    event_date_str = request.POST.get('event_date')
    event_end_date_str = request.POST.get('event_end_date')
    
    # Validation
    if not content or not title or not event_date_str:
        response = JsonResponse({'error': 'Title, content, and event date are required'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    try:
        # Parse event dates
        event_date = datetime.fromisoformat(event_date_str.replace('Z', '+00:00'))
        event_end_date = None
        if event_end_date_str:
            event_end_date = datetime.fromisoformat(event_end_date_str.replace('Z', '+00:00'))
        
        # Create the event post
        post = Post.objects.create(
            author=request.user,
            feed=feed,
            content=content,
            title=title,
            location=location,
            post_type='event',
            privacy_level=privacy_level,
            is_urgent=is_urgent,
            event_date=event_date,
            event_end_date=event_end_date,
            is_approved=not feed.require_approval
        )
        
        # Render the post partial for HTMX
        html = render_to_string('feeds/partials/post_item.html', {
            'post': post,
            'user': request.user,
            'group': group,
            'feed': feed,
        }, request=request)
        
        # Create response with success headers
        response = HttpResponse(html)
        response['HX-Trigger'] = 'postCreated,closeModal'
        
        messages.success(request, 'Event created successfully!')
        return response
        
    except ValueError as e:
        response = JsonResponse({'error': 'Invalid date format'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    except Exception as e:
        response = JsonResponse({'error': f'Failed to create event: {str(e)}'}, status=500)
        response['HX-Reswap'] = 'none'
        return response



@login_required 
@require_http_methods(["POST"])
def toggle_post_like(request, post_id):
    """Toggle like on a post via HTMX"""
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user can view this post
    if not post.can_view(request.user):
        return JsonResponse({'error': 'Not allowed'}, status=403)
    
    like, created = PostLike.objects.get_or_create(
        user=request.user,
        post=post,
        defaults={'reaction_type': 'like'}
    )
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        # Log activity
        FeedActivity.objects.create(
            user=request.user,
            post=post,
            activity_type='like'
        )
    
    # Return updated like button
    html = render_to_string('feeds/partials/like_button.html', {
        'post': post,
        'user': request.user,
        'liked': liked
    }, request=request)
    
    return HttpResponse(html)


@login_required
@require_http_methods(["POST"])
def create_comment(request, post_id):
    """Create a comment on a post via HTMX"""
    post = get_object_or_404(Post, id=post_id)
    
    if not post.can_view(request.user):
        return JsonResponse({'error': 'Not allowed'}, status=403)
    
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')
    
    if not content:
        return JsonResponse({'error': 'Comment content is required'}, status=400)
    
    parent_comment = None
    if parent_id:
        parent_comment = get_object_or_404(Comment, id=parent_id, post=post)
    
    comment = Comment.objects.create(
        post=post,
        author=request.user,
        content=content,
        parent=parent_comment,
        is_approved=not post.feed.require_approval
    )
    
    # Log activity
    FeedActivity.objects.create(
        user=request.user,
        post=post,
        activity_type='comment'
    )
    
    # Return the comment partial
    html = render_to_string('feeds/partials/comment_item.html', {
        'comment': comment,
        'user': request.user
    }, request=request)
    
    return HttpResponse(html)


@login_required
@require_http_methods(["POST"])
def toggle_comment_like(request, comment_id):
    """Toggle like on a comment via HTMX"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if not comment.post.can_view(request.user):
        return JsonResponse({'error': 'Not allowed'}, status=403)
    
    has_liked = CommentLike.objects.filter(comment=comment, user=request.user).exists()
    
    if has_liked:
        # remove the existing like record
        CommentLike.objects.filter(comment=comment, user=request.user).delete()
        liked = False
    else:
        # create a new like record
        CommentLike.objects.create(comment=comment, user=request.user, reaction_type='like')
        liked = True
    
    # Log activity
    FeedActivity.objects.create(
        user=request.user,
        post=comment.post,
        activity_type='like'
    )
    
    # Return updated like button
    html = render_to_string('feeds/partials/comment_like_button.html', {
        'comment': comment,
        'user': request.user,
        'liked': liked
    }, request=request)
    
    return HttpResponse(html)


@login_required
def load_more_posts(request, slug):
    """Load more posts for infinite scroll via HTMX"""
    group = get_object_or_404(Group, slug=slug)
    feed = get_object_or_404(Feed, group=group)
    
    page_number = request.GET.get('page', 1)
    
    posts_queryset = Post.objects.filter(
        feed=feed,
        is_approved=True
    ).select_related('author', 'author__profile').prefetch_related(
        'media', 'likes',
        # Prefetch comments in descending order to get the latest ones for the preview
        Prefetch('comments', queryset=Comment.objects.order_by('-created_at').select_related('author__profile'))
    )
    
    # Apply privacy filtering
    if not group.is_member(request.user):
        posts_queryset = posts_queryset.filter(privacy_level='public')
    
    paginator = Paginator(posts_queryset, 10)
    posts = paginator.get_page(page_number)
    
    return render(request, 'feeds/partials/post_list.html', {
        'posts': posts,
        'user': request.user
    })
    

#-----------------------------------load_comments---------------------------------------------#

@login_required
def load_comments(request, post_id):
    """Load comments for a post via HTMX"""
    post = get_object_or_404(Post, id=post_id)
    
    if not post.can_view(request.user):
        return JsonResponse({'error': 'Not allowed'}, status=403)
    
    comments = Comment.objects.filter(
        post=post,
        parent__isnull=True,
        is_approved=True
    ).select_related('author', 'author__profile').prefetch_related('replies__author')
    
    html = render_to_string('feeds/partials/comments_list.html', {
        'comments': comments,
        'post': post,
        'user': request.user
    }, request=request)
    
    return render(request, 'feeds/partials/comments_list.html', {'comments': comments, 'post': post})


@login_required
@require_http_methods(["DELETE"])
def delete_post(request, post_id):
    """Delete a post via HTMX"""
    post = get_object_or_404(Post, id=post_id)
    
    if not post.can_delete(request.user):
        return JsonResponse({'error': 'Not allowed to delete'}, status=403)
    
    post.delete()
    return HttpResponse('')  # Empty response removes the post from DOM


@login_required 
@require_http_methods(["DELETE"])
def delete_comment(request, comment_id):
    """Delete a comment via HTMX"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if not comment.can_edit(request.user):
        return JsonResponse({'error': 'Not allowed to delete'}, status=403)
    
    comment.delete()
    return HttpResponse('')  # Empty response removes the comment from DOM


@login_required
@require_http_methods(["POST"])
def edit_comment(request, comment_id):
    """Edit a comment via HTMX"""
    comment = get_object_or_404(Comment, id=comment_id)

    if not comment.can_edit(request.user):
        return JsonResponse({'error': 'Not allowed to edit'}, status=403)

    content = request.POST.get('content', '').strip()

    if not content:
        return JsonResponse({'error': 'Comment content is required'}, status=400)

    comment.content = content
    comment.save()

    # Return the updated comment partial
    html = render_to_string('feeds/partials/comment_item.html', {
        'comment': comment,
        'user': request.user
    }, request=request)

    return HttpResponse(html)


@login_required
def get_edit_comment_form(request, comment_id):
    """Return the HTMX form for editing a comment."""
    comment = get_object_or_404(Comment, id=comment_id)

    if not comment.can_edit(request.user):
        return JsonResponse({'error': 'Not allowed to edit'}, status=403)

    html = render_to_string('feeds/partials/edit_comment_form.html', {
        'comment': comment,
        'user': request.user
    }, request=request)

    return HttpResponse(html)


@login_required
def get_comment_item(request, comment_id):
    """Return the standard comment item partial (used for canceling an edit)."""
    comment = get_object_or_404(Comment, id=comment_id)

    if not comment.post.can_view(request.user):
        return JsonResponse({'error': 'Not allowed to view'}, status=403)

    return render(request, 'feeds/partials/comment_item.html', {
        'comment': comment,
        'user': request.user
    })


@login_required
def get_media_post_modal(request, group_slug):
    """Render media post creation modal"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    if not feed.allow_posts or not feed.allow_media or not group.is_member(request.user):
        return JsonResponse({'error': 'Not allowed'}, status=403)
    
    return render(request, 'feeds/partials/create_media_post.html', {
        'group': group,
        'feed': feed,
        'post_types': ['photo', 'video'],
    })


@login_required
def get_announcement_modal(request, group_slug):
    """Render announcement creation modal"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    if not feed.allow_posts or not group.is_admin(request.user):
        return JsonResponse({'error': 'Not allowed'}, status=403)
    
    return render(request, 'feeds/partials/create_announcement.html', {
        'group': group,
        'feed': feed,
    })


@login_required
def get_event_modal(request, group_slug):
    """Render event creation modal"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    if not feed.allow_posts or not feed.allow_events or not group.is_member(request.user):
        return JsonResponse({'error': 'Not allowed'}, status=403)
    
    return render(request, 'feeds/partials/create_event.html', {
        'group': group,
        'feed': feed,
    })
