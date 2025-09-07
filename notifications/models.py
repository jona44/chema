# notifications/models.py - Complete notification system
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid


class Notification(models.Model):
    """
    Universal notification system for Chema platform
    """
    NOTIFICATION_TYPES = [
        # Memorial Notifications
        ('memorial_created', 'Memorial Created'),
        ('new_memory_posted', 'New Memory Posted'),
        ('new_condolence', 'New Condolence'),
        ('condolence_approved', 'Condolence Approved'),
        ('funeral_update', 'Funeral Update'),
        
        # Group Notifications  
        ('member_joined', 'New Member Joined'),
        ('member_approved', 'Member Request Approved'),
        ('member_left', 'Member Left Group'),
        ('group_updated', 'Group Information Updated'),
        ('invitation_received', 'Group Invitation'),
        
        # Contribution Notifications
        ('new_contribution', 'New Contribution Received'),
        ('contribution_milestone', 'Contribution Milestone'),
        ('expense_recorded', 'New Expense Recorded'),
        ('campaign_update', 'Campaign Update'),
        ('contribution_completed', 'Your Contribution Completed'),
        ('deadline_approaching', 'Deadline Approaching'),
        
        # System Notifications
        ('welcome', 'Welcome Message'),
        ('profile_incomplete', 'Complete Your Profile'),
        ('system_update', 'System Update'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    DELIVERY_METHODS = [
        ('in_app', 'In-App Notification'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('whatsapp', 'WhatsApp'),  # Future integration
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Recipient
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    
    # Notification Content
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    
    # Generic Foreign Key for related objects
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Delivery and Status
    delivery_method = models.CharField(max_length=20,choices=DELIVERY_METHODS,default='in_app')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Additional data for complex notifications
    data = models.JSONField(default=dict, blank=True)
    
    # Action URL for clickable notifications
    action_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Grouping for batch notifications
    group_key = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['notification_type', '-created_at']),
            models.Index(fields=['status', 'delivery_method']),
            models.Index(fields=['group_key']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name() or self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.read_at:
            self.read_at = timezone.now()
            self.status = 'read'
            self.save(update_fields=['read_at', 'status'])
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.sent_at = timezone.now()
        self.status = 'sent'
        self.save(update_fields=['sent_at', 'status'])
    
    @property
    def is_read(self):
        """Check if notification has been read"""
        return self.read_at is not None
    
    @property
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class NotificationPreference(models.Model):
    """
    User preferences for different notification types and delivery methods
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Memorial preferences
    memorial_created_email  = models.BooleanField(default=True)
    memorial_created_push   = models.BooleanField(default=True)
    new_memory_posted_email = models.BooleanField(default=True)
    new_memory_posted_push  = models.BooleanField(default=True)
    new_condolence_email    = models.BooleanField(default=True)
    new_condolence_push     = models.BooleanField(default=True)
    funeral_update_email    = models.BooleanField(default=True)
    funeral_update_push     = models.BooleanField(default=True)
    funeral_update_sms      = models.BooleanField(default=False)
    
    # Group preferences
    member_joined_email     = models.BooleanField(default=True)
    member_joined_push      = models.BooleanField(default=True)
    group_invitation_email  = models.BooleanField(default=True)
    group_invitation_push   = models.BooleanField(default=True)
    group_invitation_sms    = models.BooleanField(default=True)

    # Contribution preferences
    new_contribution_email    = models.BooleanField(default=True)
    new_contribution_push     = models.BooleanField(default=True)
    contribution_milestone_email = models.BooleanField(default=True)
    contribution_milestone_push  = models.BooleanField(default=True)
    deadline_approaching_email   = models.BooleanField(default=True)
    deadline_approaching_push    = models.BooleanField(default=True)
    deadline_approaching_sms     = models.BooleanField(default=True)
    
    # System preferences
    system_update_email = models.BooleanField(default=False)
    system_update_push  = models.BooleanField(default=True)
    
    # General preferences
    email_notifications_enabled = models.BooleanField(default=True)
    push_notifications_enabled  = models.BooleanField(default=True)
    sms_notifications_enabled   = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start   = models.TimeField(default='22:00') # type: ignore
    quiet_hours_end     = models.TimeField(default='07:00') # type: ignore
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.get_full_name() or self.user.username}"
    
    def is_quiet_time(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        now = timezone.now().time()
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:  # Crosses midnight
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end


class NotificationTemplate(models.Model):
    """
    Templates for different notification types
    """
    notification_type = models.CharField(
        max_length=30, 
        choices=Notification.NOTIFICATION_TYPES,
        unique=True
    )
    
    # Templates for different delivery methods
    email_subject_template = models.CharField(max_length=200, blank=True)
    email_body_template    = models.TextField(blank=True)
    sms_template = models.CharField(max_length=160, blank=True)  # SMS character limit
    push_title_template = models.CharField(max_length=100, blank=True)
    push_body_template  = models.CharField(max_length=200, blank=True)
    in_app_title_template   = models.CharField(max_length=200)
    in_app_message_template = models.TextField()
    
    # Template variables documentation
    available_variables = models.JSONField(
        default=dict,
        help_text="JSON object documenting available template variables"
    )
    
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Template for {self.get_notification_type_display()}" # type: ignore


class NotificationDeliveryLog(models.Model):
    """
    Log of notification delivery attempts
    """
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='delivery_logs'
    )
    
    delivery_method = models.CharField(max_length=20, choices=Notification.DELIVERY_METHODS)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retry', 'Retry'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    response_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    attempted_at = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Provider-specific tracking
    external_id = models.CharField(max_length=100, blank=True)  # Provider's message ID
    
    class Meta:
        ordering = ['-attempted_at']
    
    def __str__(self):
        return f"{self.notification.title} - {self.delivery_method} - {self.status}"


class NotificationBatch(models.Model):
    """
    For sending bulk notifications
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=200)
    notification_type = models.CharField(max_length=30, choices=Notification.NOTIFICATION_TYPES)
    
    # Batch targeting
    target_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    target_groups = models.JSONField(default=list, blank=True)  # Group IDs or criteria
    
    # Content
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    data_template = models.JSONField(default=dict, blank=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_notification_batches'
    )
    
    def __str__(self):
        return f"Batch: {self.name} ({self.status})"