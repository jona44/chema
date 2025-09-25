from django import template

register = template.Library()

@register.filter
def can_edit_comment(comment, user):
    return comment.can_edit(user)
