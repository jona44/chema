# feeds/signals.py - Django signals for automatic notifications
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import Post, Comment, PostLike, Poll, PollVote, PostShare
from notifications.utils import NotificationService
from notifications.models import Notification


@receiver(post_save, sender=Post)
def post_created_notification(sender, instance, created, **kwargs):
    """Send notifications when a new post is created"""
    if not created or not instance.is_approved:
        return
    
    group = instance.feed.group
    
    # Don't notify the author
    recipients = group.members.exclude(id=instance.author.id)
    
    # Determine notification type based on post type
    notification_type_map = {
        'text': 'new_memory_posted',  # Default
        'photo': 'new_memory_posted',
        'video': 'new_memory_posted',
        'event': 'funeral_update',
        'poll': 'group_updated',
        'memory': 'new_memory_posted',
        'condolence': 'new_condolence',
        'tribute': 'new_memory_posted',
    }
    
    notification_type = notification_type_map.get(instance.post_type, 'new_memory_posted')
    
    # Special handling for memorial posts
    if instance.memorial_related:
        notification_type = 'new_memory_posted'
        title = f"New memory shared for {instance.memorial_related.full_name}"
        message = f"{instance.author.get_full_name() or instance.author.username} shared a memory"
    elif instance.post_type == 'event':
        title = f"New event in {group.name}"
        message = f"{instance.author.get_full_name() or instance.author.username} created an event: {instance.title}"
    elif instance.post_type == 'condolence':
        title = f"New condolence in {group.name}"
        message = f"{instance.author.get_full_name() or instance.author.username} shared condolences"
    else:
        title = f"New post in {group.name}"
        message = f"{instance.author.get_full_name() or instance.author.username} shared: {instance.content[:100]}..."
    
    # Set priority based on post characteristics
    priority = 'normal'
    if instance.is_urgent:
        priority = 'urgent'
    elif instance.is_pinned or instance.post_type in ['event', 'condolence']:
        priority = 'high'
    
    # Create notifications for all group members
    for recipient in recipients:
        NotificationService.create_notification(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message if len(message) <= 500 else message[:497] + '...',
            related_object=instance,
            action_url=instance.get_absolute_url(),
            priority=priority,
            data={
                'group_id': group.id,
                'group_name': group.name,
                'post_type': instance.post_type,
                'author_name': instance.author.get_full_name() or instance.author.username,
                'memorial_id': instance.memorial_related.id if instance.memorial_related else None
            }
        )


@receiver(post_save, sender=Comment)
def comment_created_notification(sender, instance, created, **kwargs):
    """Notify post author and mentioned users about new comments"""
    if not created:
        return
    
    post = instance.post
    
    # Notify post author (if not commenting on their own post)
    if post.author != instance.author:
        NotificationService.create_notification(
            recipient=post.author,
            notification_type='new_condolence' if post.post_type == 'memory' else 'group_updated',
            title=f"New comment on your post",
            message=f"{instance.author.get_full_name() or instance.author.username} commented: {instance.content[:100]}...",
            related_object=post,
            action_url=f"{post.get_absolute_url()}#comment-{instance.id}",
            priority='normal',
            data={
                'group_id': post.feed.group.id,
                'post_id': post.id,
                'comment_id': instance.id,
                'commenter_name': instance.author.get_full_name() or instance.author.username
            }
        )
    
    # Notify other commenters (excluding post author and comment author)
    other_commenters = Comment.objects.filter(
        post=post
    ).exclude(
        author__in=[post.author, instance.author]
    ).values_list('author', flat=True).distinct()
    
    for commenter_id in other_commenters:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            commenter = User.objects.get(id=commenter_id)
            NotificationService.create_notification(
                recipient=commenter,
                notification_type='group_updated',
                title=f"New comment on post you commented on",
                message=f"{instance.author.get_full_name() or instance.author.username} also commented on a post",
                related_object=post,
                action_url=f"{post.get_absolute_url()}#comment-{instance.id}",
                priority='normal',
                data={
                    'group_id': post.feed.group.id,
                    'post_id': post.id,
                    'comment_id': instance.id
                }
            )
        except User.DoesNotExist:
            continue


@receiver(post_save, sender=PostLike)
def post_like_notification(sender, instance, created, **kwargs):
    """Notify post author about likes (batched)"""
    if not created or instance.post.author == instance.user:
        return
    
    post = instance.post
    
    # Only send notification for memorial posts or if it's the first like
    if post.memorial_related or post.likes_count == 1:
        reaction_text = "supported" if post.post_type == 'memory' else "liked"
        
        NotificationService.create_notification(
            recipient=post.author,
            notification_type='new_condolence' if post.memorial_related else 'group_updated',
            title=f"Someone {reaction_text} your post",
            message=f"{instance.user.get_full_name() or instance.user.username} {reaction_text} your post in {post.feed.group.name}",
            related_object=post,
            action_url=post.get_absolute_url(),
            priority='low',
            data={
                'group_id': post.feed.group.id,
                'post_id': post.id,
                'liker_name': instance.user.get_full_name() or instance.user.username,
                'reaction_type': instance.reaction_type
            }
        )


@receiver(post_save, sender=PostShare)
def post_share_notification(sender, instance, created, **kwargs):
    """Notify post author about shares"""
    if not created or instance.post.author == instance.user:
        return
    
    post = instance.post
    
    NotificationService.create_notification(
        recipient=post.author,
        notification_type='group_updated',
        title=f"Your post was shared",
        message=f"{instance.user.get_full_name() or instance.user.username} shared your post",
        related_object=post,
        action_url=post.get_absolute_url(),
        priority='low',
        data={
            'group_id': post.feed.group.id,
            'post_id': post.id,
            'sharer_name': instance.user.get_full_name() or instance.user.username,
            'share_message': instance.message
        }
    )


# Enhanced view functions with notification integration
# Add these to your existing feeds/views.py

