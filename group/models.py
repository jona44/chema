from django.db import models

# Create your models here.
# groups/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinLengthValidator
import uuid


class Category(models.Model):
    """Group categories for organization"""
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=50, blank=True, help_text="Emoji or icon class")
    color       = models.CharField(max_length=20, default="#6B7280", help_text="Hex color code")
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Group(models.Model):
    """Main Group model"""
    
    PRIVACY_CHOICES = [
        ('public', 'Public - Anyone can find and join'),
        ('private', 'Private - Invite only'),
        ('closed', 'Closed - No new members'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, validators=[MinLengthValidator(3)])
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(help_text="Tell people what this group is about")
    
    # Visual
    cover_image = models.ImageField(upload_to='group_covers/', blank=True, null=True)
    
    # Organization
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags     = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    # Location (optional)
    city    = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default="South Africa")
    is_online_only = models.BooleanField(default=False)
    
    # Settings
    privacy     = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    max_members = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for unlimited")
    requires_approval = models.BooleanField(default=False, help_text="New members need approval")
    
    # Ownership
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_groups')
    admins  = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='admin_groups', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Activity tracking
    last_activity = models.DateTimeField(auto_now_add=True)
    is_active     = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Group.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('group_detail', kwargs={'slug': self.slug})

    @property
    def member_count(self):
        return self.memberships.filter(is_active=True).count() # type: ignore

    @property
    def is_full(self):
        if self.max_members:
            return self.member_count >= self.max_members
        return False

    @property
    def tag_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    def is_admin(self, user):
        return user == self.creator or user in self.admins.all()

    def is_member(self, user):
        return self.memberships.filter(user=user, is_active=True).exists() # type: ignore

    def can_join(self, user):
        """Check if user can join this group"""
        if not user.is_authenticated:
            return False, "You must be logged in to join groups"
        
        if self.is_member(user):
            return False, "You're already a member of this group"
        
        if self.privacy == 'closed':
            return False, "This group is closed to new members"
        
        if self.is_full:
            return False, "This group has reached its maximum capacity"
        
        return True, "Can join"


class GroupMembership(models.Model):
    """Track group memberships"""
    
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('banned', 'Banned'),
    ]
    
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group    = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    user     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_memberships')
    role     = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    status   = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    joined_at   = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,blank=True,                 related_name='approved_memberships')
    is_active   = models.BooleanField(default=True)
    can_post    = models.BooleanField(default=True)
    can_comment = models.BooleanField(default=True)
    join_message = models.TextField(blank=True, help_text="Message when requesting to join")

    class Meta:
        unique_together = ['group', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} in {self.group.name} ({self.status})"

    def approve(self, approved_by_user):
        """Approve membership"""
        self.status = 'active'
        self.approved_at = timezone.now()
        self.approved_by = approved_by_user
        self.save()

    def is_admin_or_creator(self):
        return (self.role in ['admin', 'moderator'] or 
                self.user == self.group.creator)


class GroupInvitation(models.Model):
    """Track group invitations"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    id    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                related_name='sent_invitations' )
    invited_email  = models.EmailField()
    invited_user   = models.ForeignKey(settings.AUTH_USER_MODEL,   on_delete=models.CASCADE, null=True, blank=True,
                related_name='received_invitations')
    message = models.TextField(blank=True, help_text="Optional personal message")
    status  = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at   = models.DateTimeField(auto_now_add=True)
    expires_at   = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['group', 'invited_email']
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation to {self.group.name} for {self.invited_email}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Expire invitations after 7 days
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        
        # Try to link to existing user
        if not self.invited_user:
            try:
                from customuser.models import CustomUser
                self.invited_user = CustomUser.objects.get(email=self.invited_email)
            except CustomUser.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def accept(self):
        """Accept the invitation"""
        if self.is_expired:
            return False, "Invitation has expired"
        
        if self.invited_user:
            # Create or update membership
            membership, created = GroupMembership.objects.get_or_create(
                group=self.group,
                user=self.invited_user,
                defaults={'status': 'active' if not self.group.requires_approval else 'pending'}
            )
            
            self.status = 'accepted'
            self.responded_at = timezone.now()
            self.save()
            
            return True, "Invitation accepted successfully"
        
        return False, "User account not found"


class GroupPost(models.Model):
    """Posts within groups (for future expansion)"""
    
    POST_TYPES = [
        ('announcement', 'Announcement'),
        ('discussion', 'Discussion'),
        ('event', 'Event'),
        ('poll', 'Poll'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group  = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_posts')
    
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='discussion')
    title     = models.CharField(max_length=300)
    content   = models.TextField()
    
    # Flags
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"{self.title} in {self.group.name}"