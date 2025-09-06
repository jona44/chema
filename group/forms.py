# groups/forms.py
from django import forms
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from .models import Group, Category, GroupMembership


class GroupBaseForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = [
            'name', 'description', 'category', 'tags',
            'city', 'country', 'is_online_only', 'privacy',
            'max_members', 'requires_approval', 'cover_image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter group name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Describe what your group is about, what you do, and who should join...'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'fitness, outdoor, beginners, weekend (comma-separated)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Cape Town'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'value': 'South Africa'
            }),
            'privacy': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'max_members': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Leave empty for unlimited',
                'min': '2'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'accept': 'image/*'
            }),
            'requires_approval': forms.CheckboxInput(attrs={
                'class': 'rounded text-blue-600 focus:ring-blue-500'
            }),
            'is_online_only': forms.CheckboxInput(attrs={
                'class': 'rounded text-blue-600 focus:ring-blue-500'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            slug = slugify(name)
            existing = Group.objects.filter(slug=slug)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A group with this name already exists.")
        return name
    
    def clean_tags(self): # This method was duplicated below, causing the error
        tags = self.cleaned_data.get('tags', '')
        if tags: 
            # Clean and validate tags
            tag_list = [tag.strip().lower() for tag in tags.split(',') if tag.strip()]
            if len(tag_list) > 10:
                raise ValidationError("Maximum 10 tags allowed.")
            return ', '.join(tag_list)
        return tags

    def clean_max_members(self):
        max_members = self.cleaned_data.get('max_members')
        if max_members is not None and max_members < 2:
            raise ValidationError("A group must allow at least 2 members.")
        return max_members 

class GroupCreationForm(GroupBaseForm):
    pass

class GroupEditForm(GroupBaseForm):
    """Form for editing existing groups"""
    pass



class GroupSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-12 pr-4 py-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Search groups by name, topic, or location...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'City'
        })
    )


class GroupInvitationForm(forms.Form):
    """Form for inviting users to a group"""
    emails = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'rows': 4,
            'placeholder': 'Enter email addresses separated by commas or new lines'
        }),
        help_text="Separate multiple email addresses with commas or put each on a new line."
    )
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'rows': 3,
            'placeholder': 'Optional personal message to include with the invitation'
        }),
        help_text="Add a personal touch to your invitation (optional)."
    )

    def clean_emails(self):
        emails_text = self.cleaned_data.get('emails', '')
        if not emails_text.strip():
            raise ValidationError("Please enter at least one email address.")
        
        # Split by comma or newline
        import re
        email_list = re.split(r'[,\n\r]+', emails_text)
        
        # Clean and validate emails
        clean_emails = []
        for email in email_list:
            email = email.strip()
            if email:
                # Basic email validation
                try:
                    from django.core.validators import validate_email
                    validate_email(email)
                    clean_emails.append(email.lower())
                except ValidationError:
                    raise ValidationError(f"Invalid email address: {email}")
        
        if not clean_emails:
            raise ValidationError("No valid email addresses found.")
        
        if len(clean_emails) > 50:
            raise ValidationError("Maximum 50 email addresses allowed per invitation.")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_emails = []
        for email in clean_emails:
            if email not in seen:
                seen.add(email)
                unique_emails.append(email)
        
        return unique_emails


class MemberSearchForm(forms.Form):
    """Form for searching and filtering group members"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Search members by name or email...'
        })
    )
    role = forms.ChoiceField(
        required=False,
        choices=[('', 'All Roles')] + GroupMembership.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status')] + GroupMembership.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )


class TransferOwnershipForm(forms.Form):
    """Form for transferring group ownership"""
    new_owner_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500',
            'placeholder': 'Enter new owner\'s email address'
        }),
        help_text="The new owner must be an existing member of the group."
    )
    confirm_transfer = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-red-600 focus:ring-red-500'
        }),
        label='I understand this action cannot be undone and I will lose admin privileges.'
    )


class GroupJoinForm(forms.Form):
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'rows': 3,
            'placeholder': 'Optional: Tell the group admins why you want to join...'
        }),
        help_text="This message will be sent to group admins if approval is required."
    )