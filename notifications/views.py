from django.shortcuts import render, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from .models import Notification
from group.models import Group

def group_notifications_view(request, group_slug):
    group = get_object_or_404(Group, slug=group_slug)
    group_content_type = ContentType.objects.get_for_model(Group)
    
    notifications = Notification.objects.filter(
        content_type=group_content_type,
        object_id=group.id
    )
    
    context = {
        'group': group,
        'notifications': notifications,
    }
    
    return render(request, 'notifications/group_notifications.html', context)
