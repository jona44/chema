# notifications/utils.py - Utility functions for notifications
from django.template import Template, Context
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import json
import requests # type: ignore
from .models import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationDeliveryLog
)


class NotificationService:
    """Service class for creating and sending notifications"""
    
    @classmethod
    def create_notification(cls, recipient, notification_type, title, message, 
                        related_object=None, action_url=None, priority='normal',
                        data=None, delivery_method='in_app'):
        """
        Create a new notification
        
        Args:
            recipient: User object
            notification_type: Type of notification (from NOTIFICATION_TYPES)
            title: Notification title
            message: Notification message
            related_object: Related model instance (optional)
            action_url: URL for notification action (optional)
            priority: Priority level (default: 'normal')
            data: Additional JSON data (optional)
            delivery_method: How to deliver notification (default: 'in_app')
        
        Returns:
            Notification instance
        """
        
        # Get content type and object ID if related object provided
        content_type = None
        object_id = None
        if related_object:
            content_type = ContentType.objects.get_for_model(related_object)
            object_id = related_object.pk
        
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            content_type=content_type,
            object_id=object_id,
            action_url=action_url,
            priority=priority,
            data=data or {},
            delivery_method=delivery_method
        )
        
        return notification
    
    @classmethod
    def send_notification(cls, notification):
        """
        Send notification via specified delivery method
        """
        try:
            # Check user preferences
            preferences = getattr(notification.recipient, 'notification_preferences', None)
            if not preferences:
                preferences = NotificationPreference.objects.create(
                    user=notification.recipient
                )
            
            # Check if delivery method is enabled
            if not cls._is_delivery_method_enabled(notification, preferences):
                return False
            
            # Check quiet hours
            if preferences.is_quiet_time() and notification.priority not in ['high', 'urgent']:
                return False
            
            # Send based on delivery method
            if notification.delivery_method == 'email':
                return cls._send_email(notification)
            elif notification.delivery_method == 'sms':
                return cls._send_sms(notification)
            elif notification.delivery_method == 'push':
                return cls._send_push(notification)
            elif notification.delivery_method == 'in_app':
                # In-app notifications are created and ready
                notification.mark_as_sent()
                return True
                
        except Exception as e:
            cls._log_delivery_failure(notification, str(e))
            return False
    
    @classmethod
    def _is_delivery_method_enabled(cls, notification, preferences):
        """Check if delivery method is enabled for user"""
        method_map = {
            'email': preferences.email_notifications_enabled,
            'sms': preferences.sms_notifications_enabled,
            'push': preferences.push_notifications_enabled,
            'in_app': True  # Always enabled
        }
        return method_map.get(notification.delivery_method, False)
    
    @classmethod
    def _send_email(cls, notification):
        """Send email notification"""
        try:
            template = NotificationTemplate.objects.get(
                notification_type=notification.notification_type,
                is_active=True
            )
            
            # Render templates
            context = Context({
                'user': notification.recipient,
                'notification': notification,
                **notification.data
            })
            
            subject_template = Template(template.email_subject_template)
            body_template = Template(template.email_body_template)
            
            subject = subject_template.render(context)
            body = body_template.render(context)
            
            # Send email
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient.email],
                fail_silently=False
            )
            
            notification.mark_as_sent()
            cls._log_delivery_success(notification, 'email')
            return True
            
        except Exception as e:
            cls._log_delivery_failure(notification, str(e), 'email')
            return False
    
    @classmethod
    def _send_sms(cls, notification):
        """Send SMS notification - integrate with South African SMS providers"""
        # This is a placeholder for SMS integration
        # You would integrate with providers like:
        # - Clickatell (popular in SA)
        # - SMSPortal
        # - Twilio
        
        try:
            # Example integration with SMS provider
            phone_number = getattr(notification.recipient, 'phone_number', None)
            if not phone_number:
                raise Exception("User has no phone number")
            
            template = NotificationTemplate.objects.get(
                notification_type=notification.notification_type,
                is_active=True
            )
            
            context = Context({
                'user': notification.recipient,
                'notification': notification,
                **notification.data
            })
            
            sms_template = Template(template.sms_template)
            message = sms_template.render(context)
            
            # Truncate to SMS limit
            if len(message) > 160:
                message = message[:157] + '...'
            
            # Send SMS via your provider
            # response = your_sms_provider.send_sms(phone_number, message)
            
            notification.mark_as_sent()
            cls._log_delivery_success(notification, 'sms')
            return True
            
        except Exception as e:
            cls._log_delivery_failure(notification, str(e), 'sms')
            return False
    
    @classmethod
    def _send_push(cls, notification):
        """Send push notification"""
        # Placeholder for push notification integration
        # You would integrate with services like:
        # - Firebase Cloud Messaging (FCM)
        # - OneSignal
        # - Pusher
        
        try:
            template = NotificationTemplate.objects.get(
                notification_type=notification.notification_type,
                is_active=True
            )
            
            context = Context({
                'user': notification.recipient,
                'notification': notification,
                **notification.data
            })
            
            title_template = Template(template.push_title_template)
            body_template = Template(template.push_body_template)
            
            title = title_template.render(context)
            body = body_template.render(context)
            
            # Send push notification via your provider
            # response = your_push_provider.send_notification(
            #     user_token, title, body, notification.action_url
            # )
            
            notification.mark_as_sent()
            cls._log_delivery_success(notification, 'push')
            return True
            
        except Exception as e:
            cls._log_delivery_failure(notification, str(e), 'push')
            return False
    
    @classmethod
    def _log_delivery_success(cls, notification, method):
        """Log successful delivery"""
        NotificationDeliveryLog.objects.create(
            notification=notification,
            delivery_method=method,
            status='success',
            delivered_at=timezone.now()
        )
    
    @classmethod
    def _log_delivery_failure(cls, notification, error_message, method=None):
        """Log delivery failure"""
        NotificationDeliveryLog.objects.create(
            notification=notification,
            delivery_method=method or notification.delivery_method,
            status='failed',
            error_message=error_message
        )
        
        # Update notification status
        notification.status = 'failed'
        notification.save(update_fields=['status'])


# Convenience functions for common notification types
def notify_memorial_created(memorial, users=None):
    """Send notification when memorial is created"""
    if not users:
        # Get family members or relevant users
        users = []  # Define your logic here
    
    for user in users:
        NotificationService.create_notification(
            recipient=user,
            notification_type='memorial_created',
            title=f'New Memorial Created',
            message=f'A memorial for {memorial.name} has been created.',
            related_object=memorial,
            action_url=f'/memorials/{memorial.id}/',
            priority='normal'
        )


def notify_new_contribution(contribution, group_members):
    """Send notification for new contribution"""
    for member in group_members:
        if member != contribution.contributor:  # Don't notify contributor
            NotificationService.create_notification(
                recipient=member,
                notification_type='new_contribution',
                title='New Contribution Received',
                message=f'{contribution.contributor.get_full_name()} contributed R{contribution.amount}',
                related_object=contribution,
                action_url=f'/contributions/{contribution.id}/',
                priority='normal'
            )