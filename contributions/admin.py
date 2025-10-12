from django.contrib import admin
from django.utils.html import format_html
from .models import ContributionCampaign, Contribution, ExpenseRecord, ContributionUpdate


class ContributionInline(admin.TabularInline):
    """Inline view for contributions within a campaign."""
    model = Contribution
    extra = 0
    fields = ('contributor_name', 'amount', 'status', 'created_at')
    readonly_fields = ('contributor_name', 'amount', 'status', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ContributionCampaign)
class ContributionCampaignAdmin(admin.ModelAdmin):
    """Admin configuration for ContributionCampaign model."""
    list_display = (
        'title', 'group', 'status', 'target_amount',
        'current_amount', 'progress_percentage_display', 'created_by', 'created_at'
    )
    list_filter = ('status', 'public_updates', 'created_at', 'group__category')
    search_fields = ('title', 'group__name', 'created_by__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'current_amount')
    inlines = [ContributionInline]

    fieldsets = (
        ('Core Information', {
            'fields': ('id', 'title', 'group', 'memorial')
        }),
        ('Campaign Details', {
            'fields': ('description', 'status', 'public_updates')
        }),
        ('Financials', {
            'fields': ('target_amount', 'current_amount')
        }),
        ('Dates', {
            'fields': ('deadline', 'funeral_date')
        }),
        ('Management', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def progress_percentage_display(self, obj):
        return format_html(
            '<progress value="{}" max="100" style="width: 100px;"></progress>&nbsp;{:.2f}%',
            obj.progress_percentage, obj.progress_percentage
        )
    progress_percentage_display.short_description = 'Progress'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('group', 'created_by', 'memorial')


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    """Admin configuration for Contribution model."""
    list_display = (
        'display_name', 'campaign', 'amount', 'currency', 'status',
        'payment_method', 'completed_at'
    )
    list_filter = ('status', 'payment_method', 'is_anonymous', 'campaign__group')
    search_fields = ('contributor_name', 'contributor_email', 'campaign__title', 'transaction_id')
    readonly_fields = ('id', 'created_at', 'completed_at')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('campaign', 'contributor')


@admin.register(ExpenseRecord)
class ExpenseRecordAdmin(admin.ModelAdmin):
    """Admin configuration for ExpenseRecord model."""
    list_display = (
        'description', 'campaign', 'category', 'amount',
        'date_incurred', 'recorded_by'
    )
    list_filter = ('category', 'date_incurred', 'campaign__group')
    search_fields = ('description', 'vendor_name', 'campaign__title')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'date_incurred'


@admin.register(ContributionUpdate)
class ContributionUpdateAdmin(admin.ModelAdmin):
    """Admin configuration for ContributionUpdate model."""
    list_display = (
        'title', 'campaign', 'update_type', 'is_public',
        'created_by', 'created_at'
    )
    list_filter = ('update_type', 'is_public', 'campaign__group')
    search_fields = ('title', 'message', 'campaign__title')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'
