# feeds/views.py - Memorial-specific post views

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils import timezone
from memorial.models import Memorial

from .models import Feed, Post, PostMedia
from group.models import Group



@login_required
@require_http_methods(["POST"])
def create_memory_post_view(request, group_slug):
    """Create a memory/story post for memorial groups"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    # Check if group has a memorial
    try:
        memorial = Memorial.objects.get(associated_group=group)

    except Memorial.DoesNotExist:
        response = JsonResponse({'error': 'This group does not have a memorial'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    # Check permissions
    if not feed.allow_posts or not group.is_member(request.user):
        response = JsonResponse({'error': 'Not allowed to post'}, status=403)
        response['HX-Reswap'] = 'none'
        return response
    
    # Get form data
    content = request.POST.get('content', '').strip()
    title = request.POST.get('title', '').strip()
    privacy_level = request.POST.get('privacy_level', 'public')
    memory_date = request.POST.get('memory_date', '')  # When the memory took place
    is_anonymous = request.POST.get('is_anonymous') == 'on'
    
    # Optional media
    media_files = request.FILES.getlist('media_files')
    
    # Validation
    if not content:
        response = JsonResponse({'error': 'Memory content is required'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    try:
        # Create the memory post
        post = Post.objects.create(
            author=request.user,
            feed=feed,
            content=content,
            title=title if title else None,
            post_type='memory',
            privacy_level=privacy_level,
            is_anonymous=is_anonymous,
            memorial_related=memorial,
            is_approved=not feed.require_approval
        )
        
        # Process media files if any
        from .utils import process_media_file, validate_media_file
        for media_file in media_files:
            if validate_media_file(media_file, 'photo'):
                processed_file, thumbnail, metadata = process_media_file(media_file, 'photo')
                PostMedia.objects.create(
                    post=post,
                    media_type='image',
                    file=processed_file,
                    thumbnail=thumbnail,
                    file_size=metadata.get('file_size', 0),
                    uploaded_by=request.user
                )
        
        # Render the post partial
        html = render_to_string('feeds/partials/post_item.html', {
            'post': post,
            'user': request.user,
            'group': group,
            'feed': feed,
        }, request=request)
        
        response = HttpResponse(html)
        response['HX-Trigger'] = 'postCreated,closeModal'
        messages.success(request, 'Memory shared successfully!')
        return response
        
    except Exception as e:
        response = JsonResponse({'error': f'Failed to create memory: {str(e)}'}, status=500)
        response['HX-Reswap'] = 'none'
        return response


@login_required
@require_http_methods(["POST"])
def create_condolence_post_view(request, group_slug):
    """Create a condolence message for memorial groups"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    # Check if group has a memorial
    try:
        memorial = Memorial.objects.get(group=group)
    except Memorial.DoesNotExist:
        response = JsonResponse({'error': 'This group does not have a memorial'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    # Check permissions
    if not feed.allow_posts or not group.is_member(request.user):
        response = JsonResponse({'error': 'Not allowed to post'}, status=403)
        response['HX-Reswap'] = 'none'
        return response
    
    # Get form data
    content = request.POST.get('content', '').strip()
    privacy_level = request.POST.get('privacy_level', 'public')
    is_anonymous = request.POST.get('is_anonymous') == 'on'
    relationship = request.POST.get('relationship', '')  # e.g., "Friend", "Colleague"
    
    # Validation
    if not content:
        response = JsonResponse({'error': 'Condolence message is required'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    try:
        # Create the condolence post
        post = Post.objects.create(
            author=request.user,
            feed=feed,
            content=content,
            title=relationship if relationship else None,  # Store relationship in title
            post_type='condolence',
            privacy_level=privacy_level,
            is_anonymous=is_anonymous,
            memorial_related=memorial,
            is_approved=True  # Condolences are auto-approved
        )
        
        # Render the post partial
        html = render_to_string('feeds/partials/post_item.html', {
            'post': post,
            'user': request.user,
            'group': group,
            'feed': feed,
        }, request=request)
        
        response = HttpResponse(html)
        response['HX-Trigger'] = 'postCreated,closeModal'
        messages.success(request, 'Condolence message sent!')
        return response
        
    except Exception as e:
        response = JsonResponse({'error': f'Failed to send condolence: {str(e)}'}, status=500)
        response['HX-Reswap'] = 'none'
        return response


@login_required
@require_http_methods(["POST"])
def create_tribute_post_view(request, group_slug):
    """Create a tribute/poem for memorial groups"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    # Check if group has a memorial
    try:
        memorial = Memorial.objects.get(group=group)
    except Memorial.DoesNotExist:
        response = JsonResponse({'error': 'This group does not have a memorial'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    # Check permissions
    if not feed.allow_posts or not group.is_member(request.user):
        response = JsonResponse({'error': 'Not allowed to post'}, status=403)
        response['HX-Reswap'] = 'none'
        return response
    
    # Get form data
    content = request.POST.get('content', '').strip()
    title = request.POST.get('title', '').strip()
    privacy_level = request.POST.get('privacy_level', 'public')
    tribute_type = request.POST.get('tribute_type', 'poem')  # poem, letter, song, etc.
    is_anonymous = request.POST.get('is_anonymous') == 'on'
    
    # Validation
    if not content or not title:
        response = JsonResponse({'error': 'Title and content are required for tributes'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    try:
        # Create the tribute post
        post = Post.objects.create(
            author=request.user,
            feed=feed,
            content=content,
            title=title,
            post_type='tribute',
            privacy_level=privacy_level,
            is_anonymous=is_anonymous,
            memorial_related=memorial,
            is_approved=not feed.require_approval
        )
        
        # Render the post partial
        html = render_to_string('feeds/partials/post_item.html', {
            'post': post,
            'user': request.user,
            'group': group,
            'feed': feed,
        }, request=request)
        
        response = HttpResponse(html)
        response['HX-Trigger'] = 'postCreated,closeModal'
        messages.success(request, 'Tribute posted successfully!')
        return response
        
    except Exception as e:
        response = JsonResponse({'error': f'Failed to create tribute: {str(e)}'}, status=500)
        response['HX-Reswap'] = 'none'
        return response


@login_required
@require_http_methods(["POST"])
def create_funeral_update_view(request, group_slug):
    """Create funeral/service update - Admin only"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    # Check if group has a memorial
    try:
        memorial = Memorial.objects.get(group=group)
    except Memorial.DoesNotExist:
        response = JsonResponse({'error': 'This group does not have a memorial'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    # Check permissions - only memorial admins can post funeral updates
    if not memorial.is_admin(request.user) and not group.is_admin(request.user):
        response = JsonResponse({'error': 'Only memorial administrators can post funeral updates'}, status=403)
        response['HX-Reswap'] = 'none'
        return response
    
    # Get form data
    content = request.POST.get('content', '').strip()
    title = request.POST.get('title', '').strip()
    location = request.POST.get('location', '').strip()
    service_date = request.POST.get('service_date', '')
    service_end_date = request.POST.get('service_end_date', '')
    is_urgent = request.POST.get('is_urgent') == 'on'
    is_pinned = request.POST.get('is_pinned') == 'on'
    
    # Validation
    if not content or not title:
        response = JsonResponse({'error': 'Title and content are required for funeral updates'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    try:
        # Parse service dates if provided
        from datetime import datetime
        event_date = None
        event_end_date = None
        
        if service_date:
            event_date = datetime.fromisoformat(service_date.replace('Z', '+00:00'))
        if service_end_date:
            event_end_date = datetime.fromisoformat(service_end_date.replace('Z', '+00:00'))
        
        # Create the funeral update post
        post = Post.objects.create(
            author=request.user,
            feed=feed,
            content=content,
            title=title,
            location=location,
            post_type='funeral_update',
            privacy_level='public',  # Funeral updates are always public to group
            is_urgent=is_urgent,
            is_pinned=is_pinned,
            event_date=event_date,
            event_end_date=event_end_date,
            memorial_related=memorial,
            is_approved=True  # Admin posts are auto-approved
        )
        
        # Render the post partial
        html = render_to_string('feeds/partials/post_item.html', {
            'post': post,
            'user': request.user,
            'group': group,
            'feed': feed,
        }, request=request)
        
        response = HttpResponse(html)
        response['HX-Trigger'] = 'postCreated,closeModal'
        messages.success(request, 'Funeral update posted successfully!')
        return response
        
    except ValueError as e:
        response = JsonResponse({'error': 'Invalid date format'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    except Exception as e:
        response = JsonResponse({'error': f'Failed to create funeral update: {str(e)}'}, status=500)
        response['HX-Reswap'] = 'none'
        return response


# Modal rendering views
@login_required
def get_memory_modal(request, group_slug):
    """Render memory post creation modal"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    try:
        memorial = Memorial.objects.get(group=group)
    except Memorial.DoesNotExist:
        return JsonResponse({'error': 'No memorial found'}, status=404)
    
    if not feed.allow_posts or not group.is_member(request.user):
        return JsonResponse({'error': 'Not allowed'}, status=403)
    
    return render(request, 'feeds/modals/create_memory.html', {
        'group': group,
        'feed': feed,
        'memorial': memorial,
    })


@login_required
def get_condolence_modal(request, group_slug):
    """Render condolence message creation modal"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    try:
        memorial = Memorial.objects.get(group=group)
    except Memorial.DoesNotExist:
        return JsonResponse({'error': 'No memorial found'}, status=404)
    
    if not feed.allow_posts or not group.is_member(request.user):
        return JsonResponse({'error': 'Not allowed'}, status=403)
    
    return render(request, 'feeds/modals/create_condolence.html', {
        'group': group,
        'feed': feed,
        'memorial': memorial,
    })


@login_required
def get_tribute_modal(request, group_slug):
    """Render tribute/poem creation modal"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    try:
        memorial = Memorial.objects.get(group=group)
    except Memorial.DoesNotExist:
        return JsonResponse({'error': 'No memorial found'}, status=404)
    
    if not feed.allow_posts or not group.is_member(request.user):
        return JsonResponse({'error': 'Not allowed'}, status=403)
    
    return render(request, 'feeds/modals/create_tribute.html', {
        'group': group,
        'feed': feed,
        'memorial': memorial,
    })


@login_required
def get_funeral_update_modal(request, group_slug):
    """Render funeral update creation modal"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    try:
        memorial = Memorial.objects.get(associated_group=group)
    except Memorial.DoesNotExist:
        return JsonResponse({'error': 'No memorial found'}, status=404)
    
    if not memorial.is_admin(request.user) and not group.is_admin(request.user):
        return JsonResponse({'error': 'Not allowed'}, status=403)
    
    return render(request, 'feeds/modals/create_funeral_update.html', {
        'group': group,
        'feed': feed,
        'memorial': memorial,
    })

    



