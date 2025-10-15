from django import template

register = template.Library()

@register.filter(name='can_edit')
def can_edit(post, user=None):
    """Return the can_edit boolean attribute if present."""
    return getattr(post, 'can_edit', False)

@register.filter(name='can_delete')
def can_delete(post, user=None):
    """Return the can_delete boolean attribute if present."""
    return getattr(post, 'can_delete', False)


# Check if user has liked the post
@register.filter(name='has_liked_post')
def has_liked_post(post, user):
    """Return True if the user has liked the post, else False."""
    if not user or not user.is_authenticated:
        return False
    # Use the related_name 'likes' for PostLike
    return post.likes.filter(user=user).exists()
