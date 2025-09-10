# memorial/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from .models import Memorial, Post, Comment, CondolenceMessage, FuneralUpdate, PostImage


class MemorialCreationForm(forms.ModelForm):
    deceased_user = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Select from group members (optional)",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )

    class Meta:
        model = Memorial
        fields = [
            'deceased_user',  # <-- new logical field, not in the model
            'full_name', 'date_of_birth', 'date_of_death', 'photo', 'biography',
            'location_of_death', 'burial_location', 'cultural_background',
            'religious_affiliation', 'traditional_names', 'funeral_date',
            'funeral_venue', 'funeral_details', 'is_public',
            'allow_condolences', 'allow_memories', 'allow_photos'
        ]
        
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Full name of the deceased'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
            'date_of_death': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
            'biography': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 6,
                'placeholder': 'Share their life story, achievements, and the impact they had on others...'
            }),
            'location_of_death': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'City, Hospital, or location where they passed'
            }),
            'burial_location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Cemetery, family burial ground, or final resting place'
            }),
            'cultural_background': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Zulu, Xhosa, Shona, Kikuyu, etc.'
            }),
            'religious_affiliation': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Christian, Muslim, Traditional, etc.'
            }),
            'traditional_names': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Clan names, praise names, traditional titles'
            }),
            'funeral_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'datetime-local'
            }),
            'funeral_venue': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Church, community hall, family home, etc.'
            }),
            'funeral_details': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Service details, dress code, directions, contact information...'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        group = kwargs.pop("group", None)
        super().__init__(*args, **kwargs)

        if group:
            self.fields["deceased_user"].queryset = group.members # type: ignore

    def clean_date_of_death(self):
        date_of_death = self.cleaned_data.get('date_of_death')
        if date_of_death and date_of_death > date.today():
            raise ValidationError("Date of death cannot be in the future.")
        return date_of_death

    def clean(self):
        cleaned_data = super().clean()
        date_of_birth = cleaned_data.get('date_of_birth')
        date_of_death = cleaned_data.get('date_of_death')

        if date_of_birth and date_of_death and date_of_birth >= date_of_death:
            raise ValidationError("Date of death must be after date of birth.")

        return cleaned_data


class PostForm(forms.ModelForm):
    class MultiFileInput(forms.ClearableFileInput):
        allow_multiple_selected = True

    images = forms.FileField(
        widget=MultiFileInput(attrs={
            'multiple': True,
            'accept': 'image/*',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        }),
        required=False,
        help_text="Select multiple images to share (optional)"
    )

    class Meta:
        model = Post
        fields = ['post_type', 'title', 'content', 'is_anonymous', 'is_family_only']
        
        widgets = {
            'post_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Give your post a title (optional)'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 6,
                'placeholder': 'Share your memory, thoughts, or message...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom styling for checkboxes
        self.fields['is_anonymous'].widget.attrs.update({
            'class': 'rounded text-blue-600 focus:ring-blue-500'
        })
        self.fields['is_family_only'].widget.attrs.update({
            'class': 'rounded text-blue-600 focus:ring-blue-500'
        })

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if len(content) < 10:
            raise ValidationError("Please write at least 10 characters.")
        return content


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'is_anonymous']
        
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Share your thoughts...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_anonymous'].widget.attrs.update({
            'class': 'rounded text-blue-600 focus:ring-blue-500'
        })


class CondolenceForm(forms.ModelForm):
    class Meta:
        model = CondolenceMessage
        fields = [
            'author_name', 'author_relationship', 'message', 
            'is_anonymous', 'language', 'includes_prayer', 'includes_blessing'
        ]
        
        widgets = {
            'author_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Your name (optional if you prefer to use your profile name)'
            }),
            'author_relationship': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Friend, Colleague, Neighbor, Family, etc.'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 6,
                'placeholder': 'Share your condolence message, memory, or words of comfort...'
            }),
            'language': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'English, Zulu, Xhosa, Shona, etc.'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style checkboxes
        checkbox_fields = ['is_anonymous', 'includes_prayer', 'includes_blessing']
        for field_name in checkbox_fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'rounded text-blue-600 focus:ring-blue-500'
            })

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 20:
            raise ValidationError("Please write a meaningful condolence message (at least 20 characters).")
        return message


class FuneralUpdateForm(forms.ModelForm):
    class Meta:
        model = FuneralUpdate
        fields = ['update_type', 'title', 'content', 'is_urgent', 'is_pinned']
        
        widgets = {
            'update_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Update title or headline'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 5,
                'placeholder': 'Provide detailed information about this update...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        checkbox_fields = ['is_urgent', 'is_pinned']
        for field_name in checkbox_fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'rounded text-red-600 focus:ring-red-500'
            })


class MemorialEditForm(forms.ModelForm):
    """Form for editing memorial information by family admins"""
    class Meta:
        model = Memorial
        fields = [
            'photo', 'biography', 'burial_location', 'funeral_date', 
            'funeral_venue', 'funeral_details', 'is_public', 
            'allow_condolences', 'allow_memories', 'allow_photos'
        ]
        
        widgets = {
            'biography': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 6
            }),
            'burial_location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'funeral_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'datetime-local'
            }),
            'funeral_venue': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'funeral_details': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4
            }),
            'photo': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        checkbox_fields = ['is_public', 'allow_condolences', 'allow_memories', 'allow_photos']
        for field_name in checkbox_fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'rounded text-blue-600 focus:ring-blue-500'
            })


class BulkCondolenceApprovalForm(forms.Form):
    """Form for bulk approving condolence messages"""
    condolence_ids = forms.CharField(widget=forms.HiddenInput())
    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve Selected'),
            ('reject', 'Reject Selected'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'text-blue-600 focus:ring-blue-500'
        })
    )

    def clean_condolence_ids(self):
        ids = self.cleaned_data.get('condolence_ids', '')
        if not ids.strip():
            raise ValidationError("No condolences selected.")
        
        try:
            # Validate that all IDs are valid UUIDs
            import uuid
            id_list = [id.strip() for id in ids.split(',') if id.strip()]
            for id_str in id_list:
                uuid.UUID(id_str)  # This will raise ValueError if invalid
            return id_list
        except ValueError:
            raise ValidationError("Invalid condolence IDs provided.")


class QuickPostForm(forms.Form):
    """Simplified form for quick posting from memorial page"""
    post_type = forms.ChoiceField(
        choices=[
            ('memory', 'Share a Memory'),
            ('condolence', 'Condolence'),
            ('photo', 'Share Photos'),
            ('tribute', 'Tribute/Poem'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'rows': 4,
            'placeholder': 'Share your thoughts, memories, or condolences...'
        }),
        max_length=2000
    )
    is_anonymous = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500'
        }),
        label='Post anonymously'
    )