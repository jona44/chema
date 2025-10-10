from django.contrib import admin
from .models import Memorial


@admin.register(Memorial)
class MemorialAdmin(admin.ModelAdmin):
    """Admin configuration for the Memorial model."""
    list_display = (
        '__str__',
        'associated_group',
        'created_by',
        'is_public',
        'created_at'
    )
    list_filter = ('is_public', 'created_at', 'associated_group__category')
    search_fields = (
        'deceased__user__email',
        'deceased__first_name',
        'deceased__surname',
        'associated_group__name'
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    filter_horizontal = ('family_admins',)

    fieldsets = (
        ('Core Information', {
            'fields': ('id', 'deceased', 'associated_group', 'created_by')
        }),
        ('Memorial Details', {
            'fields': ('photo', 'biography', 'location_of_death', 'burial_location')
        }),
        ('Funeral Details', {
            'fields': ('funeral_date', 'funeral_venue', 'funeral_details')
        }),
        ('Management & Permissions', {
            'fields': ('family_admins', 'is_public', 'allow_condolences', 'allow_memories', 'allow_photos')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('deceased__user', 'associated_group', 'created_by')
