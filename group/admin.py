# groups/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Category, Group, GroupMembership, GroupInvitation, GroupPost
from django.db.models import Q


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'group_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'name': ['name']}
    
    def group_count(self, obj):
        return obj.groups.filter(is_active=True).count()
    group_count.short_description = 'Active Groups'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            group_count=Count('group', filter=Q(group__is_active=True))
        )


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0
    fields = ['user', 'role', 'status', 'joined_at', 'is_active']
    readonly_fields = ['joined_at']
    can_delete = True


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'creator', 'category', 'privacy', 'member_count', 
        'is_active', 'created_at', 'last_activity'
    ]
    list_filter = [
        'privacy', 'is_active', 'category', 'requires_approval', 
        'is_online_only', 'created_at'
    ]
    search_fields = ['name', 'description', 'creator__email', 'city', 'tags']
    readonly_fields = ['slug', 'created_at', 'updated_at', 'last_activity']
    filter_horizontal = ['admins']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'cover_image')
        }),
        ('Organization', {
            'fields': ('category', 'tags', 'creator', 'admins')
        }),
        ('Location', {
            'fields': ('city', 'country', 'is_online_only')
        }),
        ('Settings', {
            'fields': ('privacy', 'max_members', 'requires_approval')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at', 'last_activity')
        }),
    )
    
    inlines = [GroupMembershipInline]
    
    def member_count(self, obj):
        count = obj.memberships.filter(is_active=True, status='active').count()
        if obj.max_members:
            return format_html(
                '<span style="color: {};">{}/{}</span>',
                'red' if count >= obj.max_members else 'green',
                count,
                obj.max_members
            )
        return count
    member_count.short_description = 'Members'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'creator', 'category'
        ).prefetch_related('memberships')


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'group', 'role', 'status', 'joined_at', 
        'approved_by', 'is_active'
    ]
    list_filter = [
        'role', 'status', 'is_active', 'joined_at', 
        'can_post', 'can_comment'
    ]
    search_fields = [
        'user__email', 'group__name', 'join_message'
    ]
    readonly_fields = ['joined_at', 'approved_at']
    
    fieldsets = (
        ('Membership', {
            'fields': ('group', 'user', 'role', 'status')
        }),
        ('Approval', {
            'fields': ('approved_at', 'approved_by', 'join_message')
        }),
        ('Permissions', {
            'fields': ('is_active', 'can_post', 'can_comment')
        }),
        ('Timestamps', {
            'fields': ('joined_at',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'group', 'approved_by'
        )


@admin.register(GroupInvitation)
class GroupInvitationAdmin(admin.ModelAdmin):
    list_display = [
        'invited_email', 'group', 'invited_by', 'status', 
        'created_at', 'expires_at', 'is_expired'
    ]
    list_filter = ['status', 'created_at', 'expires_at']
    search_fields = [
        'invited_email', 'group__name', 'invited_by__email'
    ]
    readonly_fields = ['created_at', 'responded_at']
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'


@admin.register(GroupPost)
class GroupPostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'group', 'author', 'post_type', 
        'is_pinned', 'is_locked', 'created_at'
    ]
    list_filter = [
        'post_type', 'is_pinned', 'is_locked', 'is_active', 'created_at'
    ]
    search_fields = ['title', 'content', 'group__name', 'author__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'content', 'post_type')
        }),
        ('Association', {
            'fields': ('group', 'author')
        }),
        ('Moderation', {
            'fields': ('is_pinned', 'is_locked', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# Customize admin site
admin.site.site_header = "Group Management Admin"
admin.site.site_title = "Group Admin"
admin.site.index_title = "Welcome to Group Management"