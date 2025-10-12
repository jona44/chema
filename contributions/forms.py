
# contributions/forms.py

from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
from .models import ContributionCampaign, Contribution, ExpenseRecord, ContributionUpdate


class ContributionCampaignForm(forms.ModelForm):
    """Form for creating/editing a contribution campaign"""
    
    class Meta:
        model = ContributionCampaign
        fields = [
            'title', 'description', 'target_amount', 
            'deadline', 'funeral_date', 
            'public_updates', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 '
                'border border-gray-300 '
                'rounded-md focus:outline-none focus:ring-2       '
                'focus:ring-blue-500',
                'placeholder': 'e.g., Funeral Expenses for John Doe'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 '
                'border border-gray-300 '
                'rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 5,
                'placeholder': 'Explain what the contributions will be used for...'
            }),
            'target_amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 '
                'border border-gray-300 '
                'rounded-md focus:outline-none '
                'focus:ring-2 focus:ring-blue-500',
                'placeholder': '10000.00',
                'step': '0.01'
            }),
            
            
            'deadline': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 '
                'border border-gray-300 '
                'rounded-md focus:outline-none '
                'focus:ring-2 focus:ring-blue-500',
                'type': 'datetime-local'
            }),
            'funeral_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 '
                'border border-gray-300 '
                'rounded-md focus:outline-none '
                'focus:ring-2 focus:ring-blue-500',
                'type': 'datetime-local'
            }),
           
            'public_updates': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 '
                'focus:ring-blue-500 '
                'border-gray-300 rounded'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 '
                'border border-gray-300 '
                'rounded-md focus:outline-none '
                'focus:ring-2 focus:ring-blue-500'
            }),
        }
        labels = {
            'title': 'Campaign Title',
            'description': 'Campaign Description',
            'target_amount': 'Target Amount',
            'currency': 'Currency',
            'deadline': 'Contribution Deadline (Optional)',
            'funeral_date': 'Funeral Date (Optional)',
            'expense_breakdown': 'Expected Expense Breakdown (JSON)',
            'public_updates': 'Allow public to see updates',
            'status': 'Campaign Status',
        }


class ContributionForm(forms.ModelForm):
    """Form for making a contribution"""
    
    terms_accepted = forms.BooleanField(
        required=True,
        label="I agree to the terms and conditions",
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        })
    )
    
    class Meta:
        model = Contribution
        fields = [
            'amount', 'contributor_name', 'contributor_email', 
            'contributor_phone', 'payment_method', 'message',
            'is_anonymous', 'relationship_to_deceased'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '100.00',
                'step': '0.01',
                'min': '1.00'
            }),
            'contributor_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Your full name'
            }),
            'contributor_email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'your@email.com'
            }),
            'contributor_phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '+27 XX XXX XXXX'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Leave a message of support for the family (optional)...'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'relationship_to_deceased': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g., Friend, Colleague, Family'
            }),
        }
        labels = {
            'amount': 'Contribution Amount',
            'contributor_name': 'Your Name',
            'contributor_email': 'Email Address',
            'contributor_phone': 'Phone Number',
            'payment_method': 'Payment Method',
            'message': 'Message to Family',
            'is_anonymous': 'Make this contribution anonymous',
            'relationship_to_deceased': 'Your Relationship (Optional)',
        }


class QuickContributionForm(forms.Form):
    """Simplified form for quick contributions"""
    
    amount = forms.DecimalField(
        validators=[MinValueValidator(Decimal('1.00'))],
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '100.00',
            'step': '0.01'
        })
    )
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 2,
            'placeholder': 'Optional message...'
        })
    )
    is_anonymous = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        })
    )


class ExpenseRecordForm(forms.ModelForm):
    """Form for recording campaign expenses"""
    
    class Meta:
        model = ExpenseRecord
        fields = [
            'category', 'description', 'amount', 
            'date_incurred', 'vendor_name', 'notes', 'receipt_image'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'description': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Brief description of expense'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'date_incurred': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'vendor_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Name of vendor/supplier'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Additional notes...'
            }),
            'receipt_image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*'
            }),
        }
        labels = {
            'category': 'Expense Category',
            'description': 'Description',
            'amount': 'Amount Spent',
            'date_incurred': 'Date of Expense',
            'vendor_name': 'Vendor/Supplier Name',
            'notes': 'Additional Notes',
            'receipt_image': 'Upload Receipt (Optional)',
        }


class ContributionUpdateForm(forms.ModelForm):
    """Form for posting campaign updates"""
    
    class Meta:
        model = ContributionUpdate
        fields = [
            'update_type', 'title', 'message', 
            'image', 'notify_contributors', 'is_public'
        ]
        widgets = {
            'update_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Update title'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 5,
                'placeholder': 'Share an update with contributors...'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*'
            }),
            'notify_contributors': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }
        labels = {
            'update_type': 'Update Type',
            'title': 'Update Title',
            'message': 'Message',
            'image': 'Attach Image (Optional)',
            'notify_contributors': 'Send notifications to all contributors',
            'is_public': 'Make this update public',
        }