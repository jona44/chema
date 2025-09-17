# feeds/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Post, PostMedia, Poll, PollOption, Comment
from memorial.models import Memorial


class PostForm(forms.ModelForm):
    """Universal form for creating posts in any group type"""
    
    media_files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=False,
        help_text="Upload images, videos, or documents"
    )
    
    # Poll fields (only shown for poll posts)
    poll_question = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ask your question...',
            'class': 'form-control'
        })
    )
    
    poll_multiple_choice = forms.BooleanField(
        required=False,
        help_text="Allow multiple selections"
    )
    
    # Dynamic poll options (handled via JavaScript)
    poll_option_1 = forms.CharField(max_length=200, required=False)
    poll_option_2 = forms.CharField(max_length=200, required=False)
    poll_option_3 = forms.CharField(max_length=200, required=False)
    poll_option_4 = forms.CharField(max_length=200, required=False)
    poll_option_5 = forms.CharField(max_length=200, required=False)
    
    # Event fields
    event_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    
    event_end_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    
    class Meta:
        model = Post
        fields = [
            'post_type', 'title', 'content', 'link_url', 'location', 
            'privacy_level', 'is_anonymous'
        ]
        widgets = {
            'post_type': forms.Select(attrs={'class': 'form-select', 'id': 'post-type-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Give your post a title (optional)...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'What\'s on your mind?'
            }),
            'link_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Add location...'
            }),
            'privacy_level': forms.Select(attrs={'class': 'form-select'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Customize post types based on group type/permissions
        if self.group:
            available_types = list(Post.POST_TYPES)
            
            # Remove memorial types if group has no memorial
            if not hasattr(self.group, 'memorial'):
                memorial_types = ['memory', 'condolence', 'tribute', 'funeral_update']
                available_types = [(k, v) for k, v in available_types if k not in memorial_types]
            
            # Remove poll if not allowed
            if hasattr(self.group, 'feed') and not self.group.feed.allow_polls:
                available_types = [(k, v) for k, v in available_types if k != 'poll']
            
            # Remove event if not allowed
            if hasattr(self.group, 'feed') and not self.group.feed.allow_events:
                available_types = [(k, v) for k, v in available_types if k != 'event']
            
            self.fields['post_type'].choices = available_types
        
        # Customize privacy levels
        privacy_choices = list(Post.PRIVACY_LEVELS)
        if self.group and self.group.is_public:
            # Add public option for public groups
            privacy_choices.insert(0, ('group_public', 'Public to Everyone'))
        
        self.fields['privacy_level'].choices = privacy_choices
    
    def clean(self):
        cleaned_data = super().clean()
        post_type = cleaned_data.get('post_type')
        content = cleaned_data.get('content')
        link_url = cleaned_data.get('link_url')
        poll_question = cleaned_data.get('poll_question')
        event_date = cleaned_data.get('event_date')
        
        # Validate required fields based on post type
        if post_type == 'link' and not link_url:
            raise ValidationError("Link URL is required for link posts.")
        
        if post_type == 'poll':
            if not poll_question:
                raise ValidationError("Poll question is required for poll posts.")
            
            # Check if at least 2 poll options are provided
            poll_options = [
                cleaned_data.get(f'poll_option_{i}', '').strip()
                for i in range(1, 6)
            ]
            valid_options = [opt for opt in poll_options if opt]
            
            if len(valid_options) < 2:
                raise ValidationError("Polls must have at least 2 options.")
        
        if post_type == 'event' and not event_date:
            raise ValidationError("Event date is required for event posts.")
        
        # Ensure content or media is provided
        if not content and not self.files.get('media_files'):
            if post_type not in ['poll', 'event', 'link']:
                raise ValidationError("Please provide some content or attach media.")
        
        return cleaned_data
    
    def save(self, commit=True):
        post = super().save(commit=False)
        
        if commit:
            post.save()
            
            # Handle poll creation
            if post.post_type == 'poll' and self.cleaned_data.get('poll_question'):
                poll = Poll.objects.create(
                    post=post,
                    question=self.cleaned_data['poll_question'],
                    is_multiple_choice=self.cleaned_data.get('poll_multiple_choice', False)
                )
                
                # Create poll options
                for i in range(1, 6):
                    option_text = self.cleaned_data.get(f'poll_option_{i}', '').strip()
                    if option_text:
                        PollOption.objects.create(poll=poll, text=option_text)
        
        return post


class CommentForm(forms.ModelForm):
    """Form for adding comments to posts"""
    
    class Meta:
        model = Comment
        fields = ['content', 'is_anonymous']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write a comment...'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        self.post = kwargs.pop('post', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Hide anonymous option if not allowed
        if self.post and hasattr(self.post.feed, 'allow_anonymous_posts'):
            if not self.post.feed.allow_anonymous_posts:
                del self.fields['is_anonymous']


class QuickPostForm(forms.Form):
    """Quick post form for the feed header"""
    
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Share something with the group...'
        }),
        max_length=2000
    )
    
    post_type = forms.ChoiceField(
        choices=[
            ('text', 'Text Post'),
            ('photo', 'Photo'),
            ('link', 'Share Link'),
        ],
        widget=forms.HiddenInput(),
        initial='text'
    )
    
    is_anonymous = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class MediaUploadForm(forms.Form):
    """Form for uploading media to posts"""
    
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        help_text="Upload images, videos, or documents (max 10MB each)"
    ) # type: ignore
    
    def clean_files(self):
        files = self.cleaned_data['files']

        if len(files) > 10:
            raise ValidationError("Maximum 10 files allowed per post.")
        
        for file in files:
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError(f"File {file.name} is too large. Maximum size is 10MB.")
            
            # Validate file types
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'video/mp4', 'video/webm', 'video/ogg', 'video/quicktime',
                'audio/mp3', 'audio/wav', 'audio/ogg',
                'application/pdf', 'text/plain'
            ]
            
            if file.content_type not in allowed_types:
                raise ValidationError(f"File type {file.content_type} not allowed.")
        
        return files


class PollForm(forms.ModelForm):
    """Dedicated form for creating polls"""
    
    class Meta:
        model = Poll
        fields = ['question', 'is_multiple_choice', 'expires_at']
        widgets = {
            'question': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ask your question...'
            }),
            'is_multiple_choice': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'expires_at': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            })
        }


class EventPostForm(forms.ModelForm):
    """Specialized form for event posts"""
    
    class Meta:
        model = Post
        fields = [
            'title', 'content', 'location', 'event_date', 'event_end_date',
            'privacy_level'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Event description...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event location'
            }),
            'event_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'event_end_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'privacy_level': forms.Select(attrs={'class': 'form-select'})
        }
    
    def clean(self):
        cleaned_data = super().clean()
        event_date = cleaned_data.get('event_date')
        event_end_date = cleaned_data.get('event_end_date')
        
        if not event_date:
            raise ValidationError("Event date is required.")
        
        if event_end_date and event_end_date <= event_date:
            raise ValidationError("Event end date must be after start date.")
        
        return cleaned_data


class MemorialPostForm(forms.ModelForm):
    """Specialized form for memorial posts"""
    
    class Meta:
        model = Post
        fields = [
            'post_type', 'title', 'content', 'is_anonymous', 'privacy_level'
        ]
        widgets = {
            'post_type': forms.Select(
                choices=[
                    ('memory', 'Memory/Story'),
                    ('condolence', 'Condolence Message'),
                    ('tribute', 'Tribute/Poem'),
                ],
                attrs={'class': 'form-select'}
            ),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Give your memory a title (optional)...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Share your memory, condolence, or tribute...'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'privacy_level': forms.Select(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        self.memorial = kwargs.pop('memorial', None)
        super().__init__(*args, **kwargs)
        
        # Customize placeholder based on post type
        if self.initial.get('post_type') == 'condolence':
            self.fields['content'].widget.attrs['placeholder'] = \
                'Share your condolences and support for the family...'
        elif self.initial.get('post_type') == 'tribute':
            self.fields['content'].widget.attrs['placeholder'] = \
                'Share a tribute, poem, or words of honor...'


class PostSearchForm(forms.Form):
    """Form for searching posts"""
    
    q = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search posts...'
        }),
        required=False
    )
    
    post_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Post.POST_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    author = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Author name or email...'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Start date must be before end date.")
        
        return cleaned_data


class ReportPostForm(forms.Form):
    """Form for reporting inappropriate posts"""
    
    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment or Bullying'),
        ('hate_speech', 'Hate Speech'),
        ('inappropriate_content', 'Inappropriate Content'),
        ('misinformation', 'False Information'),
        ('copyright', 'Copyright Violation'),
        ('other', 'Other')
    ]
    
    reason = forms.ChoiceField(
        choices=REPORT_REASONS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please provide additional details about why you are reporting this post...'
        }),
        required=False
    )
    
    def clean_details(self):
        reason = self.cleaned_data.get('reason')
        details = self.cleaned_data.get('details', '').strip()
        
        if reason == 'other' and not details:
            raise ValidationError("Please provide details when selecting 'Other' as reason.")
        
        return details


class BulkPostActionForm(forms.Form):
    """Form for bulk actions on posts (admin use)"""
    
    ACTIONS = [
        ('approve', 'Approve Selected'),
        ('reject', 'Reject Selected'),
        ('pin', 'Pin Selected'),
        ('unpin', 'Unpin Selected'),
        ('delete', 'Delete Selected'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTIONS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    post_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    def clean_post_ids(self):
        post_ids_str = self.cleaned_data.get('post_ids', '')
        if not post_ids_str:
            raise ValidationError("No posts selected.")
        
        try:
            post_ids = [int(id.strip()) for id in post_ids_str.split(',') if id.strip()]
        except ValueError:
            raise ValidationError("Invalid post IDs.")
        
        if len(post_ids) > 50:
            raise ValidationError("Maximum 50 posts can be processed at once.")
        
        return post_ids