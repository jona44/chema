# memorial/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import uuid


class Memorial(models.Model):
    """Memorial page for the deceased - central hub for remembrance"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Deceased Information
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    date_of_death = models.DateField()
    age_at_death = models.PositiveIntegerField(blank=True, null=True)
    
    # Memorial Details
    photo = models.ImageField(upload_to='memorials/', blank=True, null=True)
    biography = models.TextField(help_text="Tell their story, achievements, and impact")
    location_of_death = models.CharField(max_length=200, blank=True)
    burial_location = models.CharField(max_length=200, blank=True)
    
    # Cultural/Religious Info
    cultural_background = models.CharField(max_length=100, blank=True)
    religious_affiliation = models.CharField(max_length=100, blank=True)
    traditional_names = models.CharField(max_length=200, blank=True, help_text="Traditional/clan names")
    
    # Funeral Details
    funeral_date = models.DateTimeField(blank=True, null=True)
    funeral_venue = models.CharField(max_length=300, blank=True)
    funeral_details = models.TextField(blank=True, help_text="Service details, dress code, etc.")
    
    # Platform Management
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_memorials')
    family_admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='administered_memorials', blank=True)
    associated_group = models.ForeignKey('group.Group', on_delete=models.CASCADE, related_name='memorial')
    
    # Settings
    is_public = models.BooleanField(default=False, help_text="Can non-group members view?")
    allow_condolences = models.BooleanField(default=True)
    allow_memories = models.BooleanField(default=True)
    allow_photos = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Memorial for {self.full_name}"

    def save(self, *args, **kwargs):
        if self.date_of_birth and self.date_of_death:
            self.age_at_death = (self.date_of_death - self.date_of_birth).days // 365
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('memorial_detail', kwargs={'pk': self.pk})

    @property
    def days_since_passing(self):
        return (timezone.now().date() - self.date_of_death).days

    def is_admin(self, user):
        return user == self.created_by or user in self.family_admins.all()


class Post(models.Model):
    """Posts within memorial/group - memories, updates, condolences"""
    
    POST_TYPES = [
        ('memory', 'Memory/Story'),
        ('condolence', 'Condolence Message'),
        ('update', 'Funeral Update'),
        ('tribute', 'Tribute/Poem'),
        ('photo', 'Photo Memory'),
        ('announcement', 'Family Announcement'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Content
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memorial_posts')
    memorial = models.ForeignKey(Memorial, on_delete=models.CASCADE, related_name='posts')
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='memory')
    
    title = models.CharField(max_length=300, blank=True)
    content = models.TextField()
    
    # Media
    images = models.ManyToManyField('PostImage', blank=True, related_name='posts')
    
    # Metadata
    is_anonymous = models.BooleanField(default=False, help_text="Hide author name")
    is_pinned = models.BooleanField(default=False)
    is_family_only = models.BooleanField(default=False, help_text="Only family admins can see")
    
    # Engagement
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"{self.get_post_type_display()} by {self.author.profile.full_name or self.author.email}" # type: ignore

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})

    def can_edit(self, user):
        return user == self.author or self.memorial.is_admin(user)

    def can_delete(self, user):
        return user == self.author or self.memorial.is_admin(user)


class PostImage(models.Model):
    """Images attached to posts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to='memorial_posts/')
    caption = models.CharField(max_length=500, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image by {self.uploaded_by.email} - {self.caption[:50]}"


class Comment(models.Model):
    """Comments on memorial posts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memorial_comments')
    
    content = models.TextField(max_length=1000)
    is_anonymous = models.BooleanField(default=False)
    
    # Nested comments (replies)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Engagement
    likes_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.profile.full_name or self.author.email}"

    def can_edit(self, user):
        return user == self.author or self.post.memorial.is_admin(user)


class PostLike(models.Model):
    """Track likes on posts"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memorial_post_likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']


class CommentLike(models.Model):
    """Track likes on comments"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memorial_comment_likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'comment']


class CondolenceMessage(models.Model):
    """Dedicated condolence messages - more formal than comments"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    memorial = models.ForeignKey(Memorial, on_delete=models.CASCADE, related_name='condolences')
    
    # Author Info (can be anonymous or from non-users)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    author_name = models.CharField(max_length=200, blank=True, help_text="For non-users or anonymous")
    author_relationship = models.CharField(max_length=100, blank=True, help_text="Friend, Colleague, Neighbor, etc.")
    
    message = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True, help_text="Family can moderate")
    
    # Cultural elements
    language = models.CharField(max_length=50, blank=True, help_text="Language of message")
    includes_prayer = models.BooleanField(default=False)
    includes_blessing = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        author_display = self.author_name if self.author_name else (
            self.author.profile.full_name if self.author else "Anonymous"
        )
        return f"Condolence from {author_display}"

    @property
    def display_name(self):
        if self.is_anonymous:
            return "Anonymous Friend"
        return self.author_name if self.author_name else (
            self.author.profile.full_name if self.author else "Anonymous"
        )


class FuneralUpdate(models.Model):
    """Official updates about funeral arrangements"""
    
    UPDATE_TYPES = [
        ('schedule', 'Schedule Update'),
        ('venue', 'Venue Information'),
        ('logistics', 'Logistics & Transport'),
        ('contribution', 'Contribution Update'),
        ('general', 'General Announcement'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    memorial = models.ForeignKey(Memorial, on_delete=models.CASCADE, related_name='updates')
    
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPES, default='general')
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Importance
    is_urgent = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-is_urgent', '-created_at']

    def __str__(self):
        return f"{self.get_update_type_display()}: {self.title}" # type: ignore


# Signal handlers for updating counts
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=PostLike)
def increment_post_likes(sender, instance, created, **kwargs):
    if created:
        instance.post.likes_count = instance.post.likes.count()
        instance.post.save(update_fields=['likes_count'])

@receiver(post_delete, sender=PostLike)
def decrement_post_likes(sender, instance, **kwargs):
    instance.post.likes_count = instance.post.likes.count()
    instance.post.save(update_fields=['likes_count'])

@receiver(post_save, sender=Comment)
def increment_comment_count(sender, instance, created, **kwargs):
    if created:
        instance.post.comments_count = instance.post.comments.count()
        instance.post.save(update_fields=['comments_count'])