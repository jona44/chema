# feeds/views.py - Poll-specific views

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import json

from .models import Feed, Post, Poll, PollOption, PollVote
from group.models import Group


@login_required
@require_http_methods(["POST"])
def create_poll_post_view(request, group_slug):
    """Create a new poll post via HTMX"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    # Check permissions
    # if not feed.allow_posts or not feed.allow_polls or not group.is_member(request.user):
    #     response = JsonResponse({'error': 'Not allowed to create polls'}, status=403)
    #     response['HX-Reswap'] = 'none'
    #     return response
    
    # Get form data
    question = request.POST.get('question', '').strip()
    content = request.POST.get('content', '').strip()  # Optional description
    privacy_level = request.POST.get('privacy_level', 'public')
    is_urgent = request.POST.get('is_urgent') == 'on'
    
    # Poll settings
    is_multiple_choice = request.POST.get('is_multiple_choice') == 'on'
    allow_other_option = request.POST.get('allow_other_option') == 'on'
    poll_duration = request.POST.get('poll_duration', '')  # In days
    
    # Poll options
    options = request.POST.getlist('options[]')
    options = [opt.strip() for opt in options if opt.strip()]
    
    # Validation
    if not question:
        response = JsonResponse({'error': 'Poll question is required'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    if len(options) < 2:
        response = JsonResponse({'error': 'Poll must have at least 2 options'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    if len(options) > 10:
        response = JsonResponse({'error': 'Poll cannot have more than 10 options'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    try:
        with transaction.atomic():
            # Calculate expiration date
            expires_at = None
            if poll_duration:
                days = int(poll_duration)
                if days > 0:
                    expires_at = timezone.now() + timedelta(days=days)
            
            # Create the poll
            poll = Poll.objects.create(
                question=question,
                is_multiple_choice=is_multiple_choice,
                allow_other_option=allow_other_option,
                expires_at=expires_at
            )
            
            # Create poll options
            for option_text in options:
                PollOption.objects.create(
                    poll=poll,
                    text=option_text
                )
            
            # Add "Other" option if enabled
            if allow_other_option:
                PollOption.objects.create(
                    poll=poll,
                    text='Other (please specify)'
                )
            
            # Create the post
            post = Post.objects.create(
                author=request.user,
                feed=feed,
                content=content,
                title=question,  # Store question in title
                post_type='poll',
                privacy_level=privacy_level,
                is_urgent=is_urgent,
                is_approved=not feed.require_approval
            )
            
            # Link poll to post (you'll need to add poll field to Post model)
            # For now, we'll use a through model or handle it separately
            # Assuming you have: post.poll = poll; post.save()
        
        # Render the post partial
        html = render_to_string('feeds/partials/post_item.html', {
            'post': post,
            'user': request.user,
            'group': group,
            'feed': feed,
        }, request=request)
        
        response = HttpResponse(html)
        response['HX-Trigger'] = 'postCreated,closeModal'
        messages.success(request, 'Poll created successfully!')
        return response
        
    except ValueError as e:
        response = JsonResponse({'error': 'Invalid poll duration'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    except Exception as e:
        response = JsonResponse({'error': f'Failed to create poll: {str(e)}'}, status=500)
        response['HX-Reswap'] = 'none'
        return response


@login_required
@require_http_methods(["POST"])
def vote_poll_view(request, post_id):
    """Vote on a poll via HTMX"""
    post = get_object_or_404(Post, id=post_id, post_type='poll')
    
    # Get the poll (assuming you have post.poll relationship)
    # poll = post.poll
    poll = get_object_or_404(Poll, id=request.POST.get('poll_id'))
    
    # Check if poll is expired
    if poll.is_expired:
        response = JsonResponse({'error': 'This poll has expired'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    # Get selected option(s)
    option_ids = request.POST.getlist('options[]')
    other_text = request.POST.get('other_text', '').strip()
    
    if not option_ids:
        response = JsonResponse({'error': 'Please select at least one option'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    # Check if single choice poll has multiple selections
    if not poll.is_multiple_choice and len(option_ids) > 1:
        response = JsonResponse({'error': 'This poll only allows one choice'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    
    try:
        with transaction.atomic():
            # Remove existing votes if changing vote
            PollVote.objects.filter(
                user=request.user,
                option__poll=poll
            ).delete()
            
            # Create new votes
            for option_id in option_ids:
                option = PollOption.objects.get(id=option_id, poll=poll)
                
                # Check if this is the "Other" option and requires text
                if option.text == 'Other (please specify)' and not other_text:
                    raise ValueError('Please specify your "Other" response')
                
                PollVote.objects.create(
                    user=request.user,
                    option=option,
                    other_text=other_text if option.text == 'Other (please specify)' else ''
                )
        
        # Refresh the poll display
        poll.refresh_from_db()
        html = render_to_string('feeds/partials/poll_results.html', {
            'poll': poll,
            'post': post,
            'user': request.user,
        }, request=request)
        
        response = HttpResponse(html)
        response['HX-Trigger'] = 'pollVoted'
        messages.success(request, 'Vote recorded!')
        return response
        
    except PollOption.DoesNotExist:
        response = JsonResponse({'error': 'Invalid poll option'}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    except ValueError as e:
        response = JsonResponse({'error': str(e)}, status=400)
        response['HX-Reswap'] = 'none'
        return response
    except Exception as e:
        response = JsonResponse({'error': f'Failed to vote: {str(e)}'}, status=500)
        response['HX-Reswap'] = 'none'
        return response


@login_required
@require_http_methods(["POST"])
def remove_poll_vote_view(request, post_id):
    """Remove vote from a poll via HTMX"""
    post = get_object_or_404(Post, id=post_id, post_type='poll')
    poll = get_object_or_404(Poll, id=request.POST.get('poll_id'))
    
    try:
        # Remove user's votes
        deleted_count = PollVote.objects.filter(
            user=request.user,
            option__poll=poll
        ).delete()[0]
        
        if deleted_count == 0:
            response = JsonResponse({'error': 'No vote to remove'}, status=400)
            response['HX-Reswap'] = 'none'
            return response
        
        # Refresh the poll display
        poll.refresh_from_db()
        html = render_to_string('feeds/partials/poll_voting.html', {
            'poll': poll,
            'post': post,
            'user': request.user,
        }, request=request)
        
        response = HttpResponse(html)
        response['HX-Trigger'] = 'pollVoteRemoved'
        messages.success(request, 'Vote removed!')
        return response
        
    except Exception as e:
        response = JsonResponse({'error': f'Failed to remove vote: {str(e)}'}, status=500)
        response['HX-Reswap'] = 'none'
        return response


@login_required
def get_poll_modal(request, group_slug):
    """Render poll creation modal"""
    group = get_object_or_404(Group, slug=group_slug)
    feed = get_object_or_404(Feed, group=group)
    
    if not feed.allow_posts or not feed.allow_polls or not group.is_member(request.user):
        return JsonResponse({'error': 'Not allowed'}, status=403)
    
    return render(request, 'feeds/modals/create_poll.html', {
        'group': group,
        'feed': feed,
    })


@login_required
def get_poll_results_view(request, poll_id):
    """Get detailed poll results via HTMX"""
    poll = get_object_or_404(Poll, id=poll_id)
    post = get_object_or_404(Post, poll=poll)
    
    # Calculate percentages and get voter details
    options_data = []
    for option in poll.options.all(): # type: ignore
        percentage = (option.votes_count / poll.total_votes * 100) if poll.total_votes > 0 else 0
        voters = option.votes.select_related('user', 'user__profile').all()[:10]  # Show first 10
        
        options_data.append({
            'option': option,
            'percentage': round(percentage, 1),
            'voters': voters,
            'has_more': option.votes_count > 10
        })
    
    # Check if current user voted
    user_vote = PollVote.objects.filter(
        user=request.user,
        option__poll=poll
    ).first()
    
    html = render_to_string('feeds/partials/poll_results_detail.html', {
        'poll': poll,
        'post': post,
        'options_data': options_data,
        'user_vote': user_vote,
    }, request=request)
    
    return HttpResponse(html)


@login_required
def get_poll_voting_view(request, poll_id):
    """Get poll voting interface via HTMX"""
    poll = get_object_or_404(Poll, id=poll_id)
    post = get_object_or_404(Post, poll=poll)
    
    html = render_to_string('feeds/partials/poll_voting.html', {
        'poll': poll,
        'post': post,
        'user': request.user,
    }, request=request)
    
    return HttpResponse(html)