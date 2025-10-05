# feeds/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import uuid


class Feed(models.Model):
    """Main feed for each group - social media style"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.OneToOneField('group.Group', on_delete=models.CASCADE, related_name='feed')
    
    # Feed Settings
    allow_posts = models.BooleanField(default=True)
    allow_media = models.BooleanField(default=True)
    allow_polls = models.BooleanField(default=True)
    allow_events = models.BooleanField(default=True)
    allow_anonymous_posts = models.BooleanField(default=False)
    
    # Moderation
    require_approval = models.BooleanField(default=False, help_text="Posts need admin approval")
    auto_moderate_keywords = models.TextField(blank=True, help_text="Comma-separated keywords to flag")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Feed for {self.group.name}"


class Post(models.Model):
    """Universal post model for all group types"""
    
    POST_TYPES = [
        # General social media posts
        ('text', 'Text Post'),
        ('photo', 'Photo Post'),
        ('video', 'Video Post'),
        ('link', 'Link Share'),
        ('poll', 'Poll'),
        ('event', 'Event'),
        ('question', 'Question'),
        ('announcement', 'Announcement'),
        
        # Memorial specific (when group has memorial)
        ('memory', 'Memory/Story'),
        ('condolence', 'Condolence Message'),
        ('tribute', 'Tribute/Poem'),
        ('funeral_update', 'Funeral Update'),
        
        # Insurance/Professional specific
        ('claim_discussion', 'Claim Discussion'),
        ('policy_question', 'Policy Question'),
        ('advice_request', 'Advice Request'),
        ('case_study', 'Case Study'),
        
        # Community specific
        ('recommendation', 'Recommendation'),
        ('help_request', 'Help Request'),
        ('marketplace', 'Buy/Sell'),
        ('job_posting', 'Job Posting'),
    ]
    
    PRIVACY_LEVELS = [
        ('public', 'Public to Group'),
        ('members_only', 'Members Only'),
        ('admins_only', 'Admins Only'),
        ('close_friends', 'Close Friends'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core Content
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, related_name='posts')
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='text')
    
    # Content fields
    title = models.CharField(max_length=500, blank=True)
    content = models.TextField(blank=True)
    
    # Link sharing
    link_url = models.URLField(blank=True)
    link_title = models.CharField(max_length=200, blank=True)
    link_description = models.TextField(blank=True)
    link_image = models.URLField(blank=True)
    
    # Location (for events, meetups, etc)
    location = models.CharField(max_length=300, blank=True)
    
    # Event specific fields
    event_date = models.DateTimeField(blank=True, null=True)
    event_end_date = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    is_anonymous = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    privacy_level = models.CharField(max_length=20, choices=PRIVACY_LEVELS, default='public')
    
    
    memorial_related = models.ForeignKey('feeds.Memorial', on_delete=models.CASCADE, null=True, blank=True, related_name='feed_posts')
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged  = models.BooleanField(default=False)
    flagged_reason = models.CharField(max_length=100, blank=True)
    
    # Engagement
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count     = models.PositiveIntegerField(default=0)
    views_count      = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-is_urgent', '-created_at']
        indexes = [
            models.Index(fields=['feed', '-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['post_type', '-created_at']),
        ]
    
    def __str__(self):
        author_name = "Anonymous" if self.is_anonymous else (
            self.author.profile.full_name if hasattr(self.author, 'profile') 
            else self.author.email
        )
        return f"{self.get_post_type_display()} by {author_name}" # type: ignore
    
    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})
    
    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        return (
            user == self.author or 
            self.feed.group.is_admin(user)
        )
    
    def can_delete(self, user):
        return self.can_edit(user)
    
    def can_view(self, user):
        """Check if user can view this post based on privacy level"""
        if not user.is_authenticated:
            return self.privacy_level == 'public' and self.feed.group.is_public
        
        if self.privacy_level == 'public':
            return self.feed.group.is_member(user) or self.feed.group.is_public
        elif self.privacy_level == 'members_only':
            return self.feed.group.is_member(user)
        elif self.privacy_level == 'admins_only':
            return self.feed.group.is_admin(user)
        elif self.privacy_level == 'close_friends':
            # Implement close friends logic
            return self.author.profile.close_friends.filter(id=user.id).exists() if hasattr(self.author, 'profile') else False
        
        return False
    
    @property
    def is_memorial_post(self):
        return self.post_type in ['memory', 'condolence', 'tribute', 'funeral_update']
    
    @property 
    def engagement_score(self):
        """Calculate engagement score for algorithmic ranking"""
        return (
            self.likes_count * 1 + 
            self.comments_count * 2 + 
            self.shares_count * 3 + 
            self.views_count * 0.1
        )


class PostMedia(models.Model):
    """Media attachments for posts"""
    
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media')
    
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='feed_media/')
    thumbnail = models.ImageField(upload_to='feed_thumbnails/', blank=True, null=True)
    
    caption = models.CharField(max_length=500, blank=True)
    alt_text = models.CharField(max_length=200, blank=True, help_text="For accessibility")
    
    # Metadata
    file_size = models.PositiveIntegerField(default=0)  # in bytes
    duration = models.PositiveIntegerField(blank=True, null=True)  # for video/audio in seconds
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']  # Maintain upload order
    
    def __str__(self):
        return f"{self.get_media_type_display()} for {self.post}" # pyright: ignore[reportAttributeAccessIssue]


class Comment(models.Model):
    """Comments on posts - universal for all post types"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    
    content = models.TextField(max_length=2000)
    is_anonymous = models.BooleanField(default=False)
    
    # Nested comments (replies)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Engagement
    likes_count = models.PositiveIntegerField(default=0)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]
    
    def __str__(self):
        author_name = "Anonymous" if self.is_anonymous else (
            self.author.profile.full_name if hasattr(self.author, 'profile') 
            else self.author.email
        )
        return f"Comment by {author_name}"
    
    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        return user == self.author or self.post.feed.group.is_admin(user)
    
    @property
    def is_reply(self):
        return self.parent is not None


class PostLike(models.Model):
    """Likes/reactions on posts"""
    
    REACTION_TYPES = [
        ('like', '👍'),
        ('love', '❤️'),
        ('haha', '😂'),
        ('wow', '😮'),
        ('sad', '😢'),
        ('angry', '😠'),
        ('care', '🤗'),  # Memorial specific
        ('pray', '🙏'),  # Memorial specific
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feed_post_likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES, default='like')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
    
    def __str__(self):
        return f"{self.get_reaction_type_display()} by {self.user.email}" # type: ignore


class CommentLike(models.Model):
    """Likes on comments"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feed_comment_likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']


class PostShare(models.Model):
    """Track post shares"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares')
    shared_to_feed = models.ForeignKey(Feed, on_delete=models.CASCADE, null=True, blank=True, related_name='shared_posts')
    message = models.TextField(max_length=500, blank=True)  # Optional message when sharing
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post', 'shared_to_feed']


class Poll(models.Model):
    """Polls attached to posts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    question = models.CharField(max_length=500)
    is_multiple_choice = models.BooleanField(default=False)
    allow_other_option = models.BooleanField(default=False)
    
    # Timing
    expires_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at
    
    @property
    def total_votes(self):
        return self.options.aggregate(total=models.Sum('votes_count'))['total'] or 0 # type: ignore


class PollOption(models.Model):
    """Poll options"""
    
    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    
    text = models.CharField(max_length=200)
    votes_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['id']


class PollVote(models.Model):
    """Individual poll votes"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    other_text = models.CharField(max_length=200, blank=True)  # If "Other" option
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'option']


class FeedActivity(models.Model):
    """Track user activity in feeds for algorithmic ranking"""
    
    ACTIVITY_TYPES = [
        ('view', 'View Post'),
        ('like', 'Like Post'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('click_link', 'Click Link'),
        ('join_event', 'Join Event'),
        ('vote_poll', 'Vote in Poll'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    
    # Context data (JSON field for flexibility)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['post', 'activity_type']),
        ]


# Signal handlers for updating counts
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=PostLike)
def increment_post_likes(sender, instance, created, **kwargs):
    if created:
        Post.objects.filter(pk=instance.post.pk).update(likes_count=models.F('likes_count') + 1)

@receiver(post_delete, sender=PostLike)
def decrement_post_likes(sender, instance, **kwargs):
    Post.objects.filter(pk=instance.post.pk).update(likes_count=models.F('likes_count') - 1)

@receiver(post_save, sender=Comment)
def increment_comment_count(sender, instance, created, **kwargs):
    if created:
        Post.objects.filter(pk=instance.post.pk).update(comments_count=models.F('comments_count') + 1)

@receiver(post_delete, sender=Comment)
def decrement_comment_count(sender, instance, **kwargs):
    Post.objects.filter(pk=instance.post.pk).update(comments_count=models.F('comments_count') - 1)

@receiver(post_save, sender=PostShare)
def increment_share_count(sender, instance, created, **kwargs):
    if created:
        Post.objects.filter(pk=instance.post.pk).update(shares_count=models.F('shares_count') + 1)

@receiver(post_delete, sender=PostShare)
def decrement_share_count(sender, instance, **kwargs):
    Post.objects.filter(pk=instance.post.pk).update(shares_count=models.F('shares_count') - 1)

@receiver(post_save, sender=PollVote)
def increment_poll_option_votes(sender, instance, created, **kwargs):
    if created:
        PollOption.objects.filter(pk=instance.option.pk).update(votes_count=models.F('votes_count') + 1)

@receiver(post_delete, sender=PollVote)
def decrement_poll_option_votes(sender, instance, **kwargs):
    PollOption.objects.filter(pk=instance.option.pk).update(votes_count=models.F('votes_count') - 1)


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
