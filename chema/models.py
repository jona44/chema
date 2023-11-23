import os
import random
from django.conf import settings
from django.db import models
from django.urls import reverse
from user.models import Profile

class Group(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    cover_image = models.ImageField(upload_to='group_cover_images', null=True, blank=True)
    admin = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_groups')
    members = models.ManyToManyField(Profile, through='GroupMembership', related_name='groups')
    
    def get_admins(self):
        return self.members.filter(groupmembership__is_admin=True)
    
    def get_total_members(self):
        return self.members.count()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('create_post', args=[str(self.id)])
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Check if this is a new group
            cover_images_dir = os.path.join(settings.STATIC_ROOT, 'group_cover_images')
            cover_images = [os.path.join('group_cover_images', file) for file in os.listdir(cover_images_dir) if file.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
            if cover_images:
                random_cover_image = random.choice(cover_images)
                self.cover_image = random_cover_image
        super().save(*args, **kwargs)

class GroupMembership(models.Model):
    member      = models.ForeignKey(Profile, on_delete=models.CASCADE)
    group       = models.ForeignKey(Group, on_delete=models.CASCADE)
    is_admin    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.member.user.username} in {self.group.name}"
    
    def get_is_admin(self):
        return self.is_admin


class Post(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=True, null=True, blank=True)

    def __str__(self):
        return f"{self.author.user.username}: {self.content}"

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.user.username}: {self.content}"

class Reply(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='replies', null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f'Reply by {self.author.user.username} -> {self.content}'

    class Meta:
        verbose_name_plural = "Replies"
        
class Dependent(models.Model):
    guardian = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100,null=True, blank=True)
    date_of_birth = models.DateField()
    relationship = models.CharField(max_length=100, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='dependents',null=True, blank=True)

    def __str__(self):
        return self.name        
