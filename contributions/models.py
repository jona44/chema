# contributions/models.py - New app for handling Chema contributions
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class ContributionCampaign(models.Model):
    """
    Main campaign for collecting Chema contributions for a group/memorial
    """
    CAMPAIGN_STATUS = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.OneToOneField('groups.Group', on_delete=models.CASCADE, related_name='contribution_campaign')
    memorial = models.ForeignKey('memorial.Memorial', on_delete=models.SET_NULL, null=True, blank=True, related_name='contribution_campaign')
    
    # Campaign Details
    title = models.CharField(max_length=200, default="Funeral Expenses Support")
    description = models.TextField(help_text="Explain what the contributions will be used for")
    
    # Financial
    target_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('10.00'))])
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='ZAR', help_text="Currency code (ZAR, USD, etc.)")
    
    # Campaign Management
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_campaigns')
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS, default='active')
    
    # Important Dates
    deadline = models.DateTimeField(null=True, blank=True, help_text="Optional deadline for contributions")
    funeral_date = models.DateTimeField(null=True, blank=True, help_text="Date of funeral service")
    
    # Transparency
    expense_breakdown = models.JSONField(default=dict, blank=True, help_text="Breakdown of expected expenses")
    public_updates = models.BooleanField(default=True, help_text="Allow contributors to see updates")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Chema for {self.group.name}"

    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return min((self.current_amount / self.target_amount) * 100, 100)
        return 0

    @property
    def remaining_amount(self):
        return max(self.target_amount - self.current_amount, Decimal('0.00'))

    @property
    def contributor_count(self):
        return self.contributions.filter(status='completed').values('contributor').distinct().count() # type: ignore

    @property
    def is_deadline_approaching(self):
        if self.deadline:
            days_left = (self.deadline - timezone.now()).days
            return 0 <= days_left <= 7
        return False

    @property
    def days_until_deadline(self):
        if self.deadline:
            return max((self.deadline - timezone.now()).days, 0)
        return None

    def can_contribute(self):
        return self.status == 'active' and (not self.deadline or timezone.now() < self.deadline)


class Contribution(models.Model):
    """
    Individual contribution to a Chema campaign
    """
    CONTRIBUTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('ecocash', 'EcoCash'),
        ('airtel_money', 'Airtel Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('stripe', 'Credit/Debit Card'),
        ('cash', 'Cash (Offline)'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(ContributionCampaign, on_delete=models.CASCADE, related_name='contributions')
    
    # Contributor Information
    contributor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    contributor_name = models.CharField(max_length=200, blank=True, help_text="Name for anonymous contributors")
    contributor_email = models.EmailField(blank=True)
    contributor_phone = models.CharField(max_length=20, blank=True)
    
    # Contribution Details
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('1.00'))])
    currency = models.CharField(max_length=3, default='ZAR')
    
    # Payment Processing
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='mpesa')
    transaction_id = models.CharField(max_length=100, blank=True, help_text="External payment system transaction ID")
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Status and Tracking
    status = models.CharField(max_length=20, choices=CONTRIBUTION_STATUS, default='pending')
    
    # Personal Touch
    message = models.TextField(blank=True, help_text="Optional message to the family")
    is_anonymous = models.BooleanField(default=False)
    
    # Relationship context
    relationship_to_deceased = models.CharField(max_length=100, blank=True, help_text="Friend, Colleague, Family, etc.")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        contributor_name = self.display_name
        return f"{contributor_name} - {self.currency} {self.amount}"

    @property
    def display_name(self):
        if self.is_anonymous:
            return "Anonymous Friend"
        return self.contributor_name if self.contributor_name else (
            self.contributor.profile.full_name if self.contributor else "Anonymous"
        )

    def complete_contribution(self, transaction_id=None):
        """Mark contribution as completed and update campaign total"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()
        
        # Update campaign total
        self.campaign.current_amount += self.amount
        self.campaign.save()


class ExpenseRecord(models.Model):
    """
    Track how Chema contributions are being used
    """
    EXPENSE_CATEGORIES = [
        ('coffin', 'Coffin/Casket'),
        ('transport', 'Transportation'),
        ('venue', 'Venue Costs'),
        ('catering', 'Food & Catering'),
        ('flowers', 'Flowers & Decorations'),
        ('printing', 'Programs & Printing'),
        ('legal', 'Legal/Documentation'),
        ('accommodation', 'Accommodation'),
        ('other', 'Other Expenses'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(ContributionCampaign, on_delete=models.CASCADE, related_name='expenses')
    
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES)
    description = models.CharField(max_length=300)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='ZAR')
    
    # Documentation
    receipt_image = models.ImageField(upload_to='expense_receipts/', blank=True)
    vendor_name = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    # Tracking
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_incurred = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_incurred', '-created_at']

    def __str__(self):
        return f"{self.get_category_display()}: {self.currency} {self.amount}" # type: ignore


class ContributionUpdate(models.Model):
    """
    Updates to keep contributors informed about campaign progress and fund usage
    """
    UPDATE_TYPES = [
        ('progress', 'Progress Update'),
        ('expense', 'Expense Report'), 
        ('milestone', 'Milestone Reached'),
        ('thank_you', 'Thank You Message'),
        ('urgent', 'Urgent Need'),
        ('completion', 'Campaign Complete'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(ContributionCampaign, on_delete=models.CASCADE, related_name='updates')
    
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPES, default='progress')
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Attachments
    image = models.ImageField(upload_to='contribution_updates/', blank=True)
    
    # Settings
    notify_contributors = models.BooleanField(default=True, help_text="Send notifications to all contributors")
    is_public = models.BooleanField(default=True, help_text="Visible to all group members")
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_update_type_display()}: {self.title}" # type: ignore


# Signals to update campaign totals
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Contribution)
def update_campaign_total_on_save(sender, instance, **kwargs):
    if instance.status == 'completed':
        # Recalculate campaign total
        total = instance.campaign.contributions.filter(status='completed').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        instance.campaign.current_amount = total
        instance.campaign.save(update_fields=['current_amount'])

@receiver(post_delete, sender=Contribution)
def update_campaign_total_on_delete(sender, instance, **kwargs):
    if instance.status == 'completed':
        # Recalculate campaign total
        total = instance.campaign.contributions.filter(status='completed').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        instance.campaign.current_amount = total
        instance.campaign.save(update_fields=['current_amount'])