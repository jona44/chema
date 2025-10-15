from django import template

register = template.Library()

@register.filter
def get_users(likes_queryset):
    """Return a list of usernames from a likes queryset"""
    return [like.user.username for like in likes_queryset]
