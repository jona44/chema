# feeds/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import (
    Feed, Post, PostMedia, Comment, PostLike, CommentLike,
    PostShare, Poll, PollOption, PollVote, FeedActivity
)


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = [
        'group', 'allow_posts', 'allow_media', 'allow_polls', 
        'allow_events', 'require_approval', 'posts_count'
    ]
    list_filter = [
        'allow_posts', 'allow_media', 'allow_polls', 'allow_events',
        'require_approval', 'created_at'
    ]
    search_fields = ['group__name']
    readonly_fields = ['created_at', 'updated_at', 'posts_count']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('group',)
        }),
        ('Permissions', {
            'fields': (
                'allow_posts', 'allow_media', 'allow_polls', 
                'allow_events', 'allow_anonymous_posts'
            )
        }),
        ('Moderation', {
            'fields': ('require_approval', 'auto_moderate_keywords')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def posts_count(self, obj):
        return obj.posts.count()
    posts_count.short_description = 'Posts'


class PostMediaInline(admin.TabularInline):
    model = PostMedia
    extra = 0
    readonly_fields = ['uploaded_at', 'file_size']


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2
    readonly_fields = ['votes_count']


class PollInline(admin.StackedInline):
    model = Poll
    extra = 0
    readonly_fields = ['created_at', 'total_votes']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'title_or_content', 'author', 'feed', 'post_type', 
        'privacy_level', 'is_pinned', 'is_approved', 'engagement_score_display',
        'created_at'
    ]
    list_filter = [
        'post_type', 'privacy_level', 'is_approved', 'is_pinned', 
        'is_urgent', 'is_flagged', 'created_at', 'feed__group__category'
    ]
    search_fields = [
        'title', 'content', 'author__email', 'author__profile__full_name'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'likes_count', 'comments_count',
        'shares_count', 'views_count', 'engagement_score_display'
    ]
    
    fieldsets = (
        ('Content', {
            'fields': ('author', 'feed', 'post_type', 'title', 'content')
        }),
        ('Media & Links', {
            'fields': ('link_url', 'link_title', 'link_description'),
            'classes': ('collapse',)
        }),
        ('Event Details', {
            'fields': ('location', 'event_date', 'event_end_date'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': (
                'privacy_level', 'is_anonymous', 'is_pinned', 
                'is_urgent', 'memorial_related'
            )
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_flagged', 'flagged_reason')
        }),
        ('Engagement', {
            'fields': (
                'likes_count', 'comments_count', 'shares_count', 
                'views_count', 'engagement_score_display'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [PostMediaInline, PollInline]
    
    actions = [
        'approve_posts', 'reject_posts', 'pin_posts', 
        'unpin_posts', 'mark_urgent', 'unmark_urgent'
    ]
    
    def title_or_content(self, obj):
        if obj.title:
            return obj.title[:50]
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    title_or_content.short_description = 'Content'
    
    def engagement_score_display(self, obj):
        score = obj.engagement_score
        if score > 100:
            color = 'green'
        elif score > 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}">{}</span>',
            color, round(score, 1)
        )
    engagement_score_display.short_description = 'Engagement'
    
    def approve_posts(self, request, queryset):
        updated = queryset.update(is_approved=True, is_flagged=False)
        self.message_user(request, f'{updated} posts approved.')
    approve_posts.short_description = 'Approve selected posts'
    
    def reject_posts(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} posts rejected.')
    reject_posts.short_description = 'Reject selected posts'
    
    def pin_posts(self, request, queryset):
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'{updated} posts pinned.')
    pin_posts.short_description = 'Pin selected posts'
    
    def unpin_posts(self, request, queryset):
        updated = queryset.update(is_pinned=False)
        self.message_user(request, f'{updated} posts unpinned.')
    unpin_posts.short_description = 'Unpin selected posts'
    
    def mark_urgent(self, request, queryset):
        updated = queryset.update(is_urgent=True)
        self.message_user(request, f'{updated} posts marked urgent.')
    mark_urgent.short_description = 'Mark as urgent'
    
    def unmark_urgent(self, request, queryset):
        updated = queryset.update(is_urgent=False)
        self.message_user(request, f'{updated} posts unmarked urgent.')
    unmark_urgent.short_description = 'Remove urgent marking'


@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    list_display = [
        'post', 'media_type', 'file_name', 'file_size_display', 
        'uploaded_by', 'uploaded_at'
    ]
    list_filter = ['media_type', 'uploaded_at']
    search_fields = ['post__title', 'caption', 'uploaded_by__email']
    readonly_fields = ['uploaded_at', 'file_size']
    
    def file_name(self, obj):
        return obj.file.name.split('/')[-1] if obj.file else 'No file'
    file_name.short_description = 'File Name'
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size > 1024 * 1024:
                return f'{obj.file_size / (1024 * 1024):.1f} MB'
            elif obj.file_size > 1024:
                return f'{obj.file_size / 1024:.1f} KB'
            else:
                return f'{obj.file_size} bytes'
        return 'Unknown'
    file_size_display.short_description = 'File Size'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'content_preview', 'author', 'post', 'parent', 
        'is_anonymous', 'is_approved', 'likes_count', 'created_at'
    ]
    list_filter = [
        'is_anonymous', 'is_approved', 'is_flagged', 'created_at'
    ]
    search_fields = [
        'content', 'author__email', 'author__profile__full_name', 'post__title'
    ]
    readonly_fields = ['created_at', 'updated_at', 'likes_count']
    
    actions = ['approve_comments', 'reject_comments']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True, is_flagged=False)
        self.message_user(request, f'{updated} comments approved.')
    approve_comments.short_description = 'Approve selected comments'
    
    def reject_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comments rejected.')
    reject_comments.short_description = 'Reject selected comments'


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = [
        'question', 'post', 'is_multiple_choice', 
        'total_votes', 'is_expired', 'created_at'
    ]
    list_filter = ['is_multiple_choice', 'created_at']
    search_fields = ['question', 'post__title']
    readonly_fields = ['created_at', 'total_votes']
    
    inlines = [PollOptionInline]
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'


@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ['text', 'poll', 'votes_count']
    list_filter = ['poll__created_at']
    search_fields = ['text', 'poll__question']
    readonly_fields = ['votes_count']


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'reaction_type', 'created_at']
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['user__email', 'post__title']
    readonly_fields = ['created_at']


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'comment__content']
    readonly_fields = ['created_at']
    
    def comment_preview(self, obj):
        return obj.comment.content[:30] + '...' if len(obj.comment.content) > 30 else obj.comment.content
    comment_preview.short_description = 'Comment'


@admin.register(PostShare)
class PostShareAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'shared_to_feed', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'post__title']
    readonly_fields = ['created_at']


@admin.register(FeedActivity)
class FeedActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'activity_type', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__email', 'post__title']
    readonly_fields = ['created_at']
    
    # Don't show this in admin menu (too much data)
    # def has_add_permission(self, request):
    #     return False


# Custom admin site configuration
admin.site.site_header = 'Social Feeds Administration'
admin.site.site_title = 'Feeds Admin'
admin.site.index_title = 'Welcome to Social Feeds Administration'

# Add some custom styling
admin.site.enable_nav_sidebar = True