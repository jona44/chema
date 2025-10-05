from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Group
from feeds.models import Feed


@receiver(post_save, sender=Group)
def create_group_feed(sender, instance, created, **kwargs):
    """
    Automatically create a Feed object whenever a new Group is created.
    """
    if created:
        Feed.objects.create(group=instance)