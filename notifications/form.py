# notifications/forms.py - Django forms for notifications
from django import forms
from django.contrib.auth import get_user_model
from .models import NotificationPreference, NotificationBatch, Notification

User = get_user_model()


class NotificationPreferenceForm(forms.ModelForm):
    """Form for user notification preferences"""
    
    class Meta:
        model = NotificationPreference
        exclude = ['user', 'created_at', 'updated_at']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Group fields for better organization in template
        self.memorial_fields = [
            'memorial_created_email', 'memorial_created_push',
            'new_memory_posted_email', 'new_memory_posted_push',
            'new_condolence_email', 'new_condolence_push',
            'funeral_update_email', 'funeral_update_push', 'funeral_update_sms'
        ]
        
        self.group_fields = [
            'member_joined_email', 'member_joined_push',
            'group_invitation_email', 'group_invitation_push', 'group_invitation_sms'
        ]
        
        self.contribution_fields = [
            'new_contribution_email', 'new_contribution_push',
            'contribution_milestone_email', 'contribution_milestone_push',
            'deadline_approaching_email', 'deadline_approaching_push', 'deadline_approaching_sms'
        ]
        
        self.system_fields = [
            'system_update_email', 'system_update_push'
        ]
        
        self.general_fields = [
            'email_notifications_enabled', 'push_notifications_enabled', 'sms_notifications_enabled'
        ]
        
        self.quiet_hours_fields = [
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end'
        ]
        
        # Add CSS classes and help text
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) 
                        else 'form-control'
            })
            
            # Add help text for SMS fields (South African context)
            if 'sms' in field_name:
                field.help_text = 'SMS notifications may incur standard messaging rates'
        
        # Time field widgets
        self.fields['quiet_hours_start'].widget = forms.TimeInput(
            attrs={'type': 'time', 'class': 'form-control'}
        )
        self.fields['quiet_hours_end'].widget = forms.TimeInput(
            attrs={'type': 'time', 'class': 'form-control'}
        )


class BulkNotificationForm(forms.Form):
    """Form for creating bulk notifications"""
    
    ACTION_CHOICES = [
        ('mark_read', 'Mark as Read'),
        ('delete', 'Delete'),
    ]
    
    action = forms.ChoiceField(choices=ACTION_CHOICES)
    notification_ids = forms.CharField(widget=forms.HiddenInput())


class NotificationBatchForm(forms.ModelForm):
    """Form for creating notification batches (admin use)"""
    
    class Meta:
        model = NotificationBatch
        fields = [
            'name', 'notification_type', 'title_template', 
            'message_template', 'data_template', 'scheduled_at'
        ]
        widgets = {
            'scheduled_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'message_template': forms.Textarea(
                attrs={'rows': 5, 'class': 'form-control'}
            ),
            'data_template': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control', 'placeholder': '{}'}
            )
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
        
        # Add help text
        self.fields['data_template'].help_text = 'JSON data for template variables (optional)'
        self.fields['scheduled_at'].help_text = 'Leave empty to send immediately'


class NotificationFilterForm(forms.Form):
    """Form for filtering notifications"""
    
    notification_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Notification.NOTIFICATION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('read', 'Read'),
            ('unread', 'Unread')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + Notification.PRIORITY_LEVELS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
