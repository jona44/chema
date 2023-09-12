import os
import random
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.conf import settings

class Admin(models.Model):
    admin       = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    date        = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    
    def __str__(self):
        return self.admin
        


class Group(models.Model):
    name        = models.CharField(max_length=100)
    members     = models.ManyToManyField(User, related_name='group_m')
    admin       = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_active   = models.BooleanField(default=True)
    admins_as_members = models.ManyToManyField(User, related_name='admin_groups', blank=True)
    description       = models.TextField(null=True, blank=True)
    date              = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    cover_image       = models.ImageField(upload_to='group_cover_images', null=True, blank=True)

    def __str__(self):
        return self.name
    
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Check if this is a new group
            # Get a list of cover image file paths from the "group_cover_images" directory
            cover_images_dir = os.path.join(settings.STATIC_ROOT, 'group_cover_images')
            cover_images = [os.path.join('group_cover_images', file) for file in os.listdir(cover_images_dir) if file.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
            if cover_images:
                # Select a random cover image path
                random_cover_image = random.choice(cover_images)
                self.cover_image = random_cover_image
        super().save(*args, **kwargs)


    def add_member(self, user):
        self.members.add(user)

    def remove_member(self, user):
        self.members.remove(user)


class Post(models.Model):
    author     = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    group      = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    content    = models.TextField(null=True, blank=True)
    image      = models.ImageField(upload_to='post_images/', null=True, blank=True)  # Add an ImageField for images
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    approved   = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return f"{self.author.username}: {self.content}"


    

class Comment(models.Model):
    post       = models.ForeignKey(Post, on_delete=models.CASCADE)
    author     = models.ForeignKey(User, on_delete=models.CASCADE)
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username}: {self.content}"

class Reply(models.Model):
    author     = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    comment    = models.ForeignKey(Comment, on_delete=models.CASCADE,related_name='replies',null=True,blank=True)
    content    = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)

    def __str__(self):
        return f'Reply by {self.author.username}  -> {self.content}'
    
    class Meta:
        verbose_name_plural = "Replies"

class Dependent(models.Model):
    guardian      = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    name          = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    relationship  = models.CharField(max_length=100 ,null=True,blank=True)
    date        = models.DateTimeField(auto_now_add=True,null=True,blank=True)


    def __str__(self):
        return self.name


