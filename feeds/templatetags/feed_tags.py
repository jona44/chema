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
