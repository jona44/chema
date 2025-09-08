# notifications/admin.py - Django admin configuration
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
from django.contrib.admin import SimpleListFilter

from .models import (
    Notification, 
    NotificationPreference, 
    NotificationTemplate, 
    NotificationDeliveryLog,
    NotificationBatch
)


class DeliveryStatusFilter(SimpleListFilter):
    """Custom filter for notification delivery status"""
    title = 'Delivery Status'
    parameter_name = 'delivery_status'

    def lookups(self, request, model_admin):
        return (
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('delivered', 'Delivered'),
            ('failed', 'Failed'),
            ('read', 'Read'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class ReadStatusFilter(SimpleListFilter):
    """Custom filter for read/unread notifications"""
    title = 'Read Status'
    parameter_name = 'read_status'

    def lookups(self, request, model_admin):
        return (
            ('read', 'Read'),
            ('unread', 'Unread'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'read':
            return queryset.filter(read_at__isnull=False)
        elif self.value() == 'unread':
            return queryset.filter(read_at__isnull=True)
        return queryset


class NotificationDeliveryLogInline(admin.TabularInline):
    """Inline for delivery logs"""
    model = NotificationDeliveryLog
    extra = 0
    readonly_fields = ['attempted_at', 'delivered_at', 'status', 'response_data', 'error_message']
    can_delete = False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'recipient_name', 
        'notification_type', 
        'priority_badge',
        'status_badge', 
        'delivery_method',
        'read_status',
        'created_at'
    ]
    
    list_filter = [
        'notification_type', 
        'priority', 
        DeliveryStatusFilter,
        ReadStatusFilter,
        'delivery_method',
        'created_at'
    ]
    
    search_fields = [
        'title', 
        'message', 
        'recipient__username', 
        'recipient__first_name', 
        'recipient__last_name',
        'recipient__email'
    ]
    
    readonly_fields = [
        'id', 
        'created_at', 
        'sent_at', 
        'read_at',
        'related_object_link'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'recipient', 'notification_type', 'priority')
        }),
        ('Content', {
            'fields': ('title', 'message', 'data', 'action_url')
        }),
        ('Delivery', {
            'fields': ('delivery_method', 'status', 'group_key')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id', 'related_object_link'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at', 'read_at', 'expires_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [NotificationDeliveryLogInline]
    
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_sent', 'mark_as_delivered', 'resend_notifications']
    
    def recipient_name(self, obj):
        """Display recipient name with link to user admin"""
        name = obj.recipient.get_full_name() or obj.recipient.username
        url = reverse('admin:auth_user_change', args=[obj.recipient.pk])
        return format_html('<a href="{}">{}</a>', url, name)
    recipient_name.short_description = 'Recipient'
    
    def priority_badge(self, obj):
        """Display priority as colored badge"""
        colors = {
            'low': '#28a745',
            'normal': '#6c757d', 
            'high': '#fd7e14',
            'urgent': '#dc3545'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'pending': '#ffc107',
            'sent': '#17a2b8',
            'delivered': '#28a745',
            'failed': '#dc3545',
            'read': '#28a745'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def read_status(self, obj):
        """Display read status with icon"""
        if obj.is_read:
            return format_html(
                '<span style="color: #28a745;">✓ Read</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">✗ Unread</span>'
            )
    read_status.short_description = 'Read'
    
    def related_object_link(self, obj):
        """Display link to related object if available"""
        if obj.related_object:
            try:
                url = reverse(
                    f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                    args=[obj.object_id]
                )
                return format_html('<a href="{}">{}</a>', url, obj.related_object)
            except:
                return str(obj.related_object)
        return '-'
    related_object_link.short_description = 'Related Object'
    
    # Admin actions
    def mark_as_sent(self, request, queryset):
        """Mark selected notifications as sent"""
        updated = queryset.filter(status='pending').update(
            status='sent',
            sent_at=timezone.now()
        )
        self.message_user(request, f'{updated} notifications marked as sent.')
    mark_as_sent.short_description = "Mark selected notifications as sent"
    
    def mark_as_delivered(self, request, queryset):
        """Mark selected notifications as delivered"""
        updated = queryset.exclude(status='delivered').update(status='delivered')
        self.message_user(request, f'{updated} notifications marked as delivered.')
    mark_as_delivered.short_description = "Mark selected notifications as delivered"
    
    def resend_notifications(self, request, queryset):
        """Reset failed notifications for resending"""
        updated = queryset.filter(status='failed').update(
            status='pending',
            sent_at=None
        )
        self.message_user(request, f'{updated} notifications reset for resending.')
    resend_notifications.short_description = "Reset failed notifications for resending"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user_name',
        'email_enabled',
        'push_enabled', 
        'sms_enabled',
        'quiet_hours_status',
        'updated_at'
    ]
    
    list_filter = [
        'email_notifications_enabled',
        'push_notifications_enabled', 
        'sms_notifications_enabled',
        'quiet_hours_enabled',
        'updated_at'
    ]
    
    search_fields = [
        'user__username',
        'user__first_name', 
        'user__last_name',
        'user__email'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('General Settings', {
            'fields': (
                'email_notifications_enabled',
                'push_notifications_enabled', 
                'sms_notifications_enabled'
            )
        }),
        ('Memorial Notifications', {
            'fields': (
                'memorial_created_email', 'memorial_created_push',
                'new_memory_posted_email', 'new_memory_posted_push',
                'new_condolence_email', 'new_condolence_push',
                'funeral_update_email', 'funeral_update_push', 'funeral_update_sms'
            )
        }),
        ('Group Notifications', {
            'fields': (
                'member_joined_email', 'member_joined_push',
                'group_invitation_email', 'group_invitation_push', 'group_invitation_sms'
            )
        }),
        ('Contribution Notifications', {
            'fields': (
                'new_contribution_email', 'new_contribution_push',
                'contribution_milestone_email', 'contribution_milestone_push',
                'deadline_approaching_email', 'deadline_approaching_push', 'deadline_approaching_sms'
            )
        }),
        ('System Notifications', {
            'fields': (
                'system_update_email', 'system_update_push'
            )
        }),
        ('Quiet Hours', {
            'fields': (
                'quiet_hours_enabled',
                'quiet_hours_start',
                'quiet_hours_end'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_name(self, obj):
        """Display user name with link"""
        name = obj.user.get_full_name() or obj.user.username
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, name)
    user_name.short_description = 'User'
    
    def email_enabled(self, obj):
        return obj.email_notifications_enabled
    email_enabled.boolean = True
    email_enabled.short_description = 'Email'
    
    def push_enabled(self, obj):
        return obj.push_notifications_enabled
    push_enabled.boolean = True
    push_enabled.short_description = 'Push'
    
    def sms_enabled(self, obj):
        return obj.sms_notifications_enabled  
    sms_enabled.boolean = True
    sms_enabled.short_description = 'SMS'
    
    def quiet_hours_status(self, obj):
        if obj.quiet_hours_enabled:
            return f"{obj.quiet_hours_start} - {obj.quiet_hours_end}"
        return "Disabled"
    quiet_hours_status.short_description = 'Quiet Hours'


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'notification_type_display',
        'is_active',
        'has_email_template',
        'has_sms_template',
        'has_push_template',
        'updated_at'
    ]
    
    list_filter = [
        'notification_type',
        'is_active',
        'updated_at'
    ]
    
    search_fields = [
        'notification_type',
        'in_app_title_template',
        'email_subject_template'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('notification_type', 'is_active', 'available_variables')
        }),
        ('In-App Templates', {
            'fields': ('in_app_title_template', 'in_app_message_template')
        }),
        ('Email Templates', {
            'fields': ('email_subject_template', 'email_body_template')
        }),
        ('SMS Template', {
            'fields': ('sms_template',),
            'description': 'SMS template is limited to 160 characters'
        }),
        ('Push Notification Templates', {
            'fields': ('push_title_template', 'push_body_template')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def notification_type_display(self, obj):
        return obj.get_notification_type_display()
    notification_type_display.short_description = 'Notification Type'
    
    def has_email_template(self, obj):
        return bool(obj.email_subject_template and obj.email_body_template)
    has_email_template.boolean = True
    has_email_template.short_description = 'Email'
    
    def has_sms_template(self, obj):
        return bool(obj.sms_template)
    has_sms_template.boolean = True
    has_sms_template.short_description = 'SMS'
    
    def has_push_template(self, obj):
        return bool(obj.push_title_template and obj.push_body_template)
    has_push_template.boolean = True
    has_push_template.short_description = 'Push'


@admin.register(NotificationDeliveryLog)
class NotificationDeliveryLogAdmin(admin.ModelAdmin):
    list_display = [
        'notification_title',
        'delivery_method',
        'status_badge',
        'attempted_at',
        'delivered_at'
    ]
    
    list_filter = [
        'delivery_method',
        'status',
        'attempted_at'
    ]
    
    search_fields = [
        'notification__title',
        'notification__recipient__username',
        'external_id'
    ]
    
    readonly_fields = [
        'notification',
        'delivery_method', 
        'attempted_at',
        'delivered_at',
        'external_id'
    ]
    
    date_hierarchy = 'attempted_at'
    
    def notification_title(self, obj):
        return obj.notification.title[:50] + '...' if len(obj.notification.title) > 50 else obj.notification.title
    notification_title.short_description = 'Notification'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'success': '#28a745',
            'failed': '#dc3545',
            'retry': '#17a2b8'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'notification_type',
        'status_badge',
        'progress_display',
        'created_by',
        'scheduled_at',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'notification_type',
        'created_at',
        'scheduled_at'
    ]
    
    search_fields = [
        'name',
        'created_by__username',
        'title_template'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'started_at', 
        'completed_at',
        'total_recipients',
        'sent_count',
        'failed_count'
    ]
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('id', 'name', 'notification_type', 'status')
        }),
        ('Content Templates', {
            'fields': ('title_template', 'message_template', 'data_template')
        }),
        ('Targeting', {
            'fields': ('target_users', 'target_groups')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at',)
        }),
        ('Statistics', {
            'fields': ('total_recipients', 'sent_count', 'failed_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Created By', {
            'fields': ('created_by',)
        })
    )
    
    filter_horizontal = ['target_users']
    
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'scheduled': '#17a2b8',
            'processing': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def progress_display(self, obj):
        """Show delivery progress as % with a badge"""
        if not obj.total_recipients:
            return format_html('<span style="color: #6c757d;">N/A</span>')
        percent = (obj.sent_count / obj.total_recipients) * 100
        color = "#28a745" if percent == 100 else "#ffc107"
        return format_html(
            '<span style="font-weight: bold; color: {}; padding: 2px 6px;">{:.0f}%</span>',
            color, percent
        )
    progress_display.short_description = "Progress"