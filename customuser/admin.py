from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display  = ['email', 'username', 'is_active', 'is_email_verified', 'date_joined']
    list_filter   = ['is_active', 'is_email_verified', 'is_staff', 'date_joined']
    search_fields  = ['email', 'username']
    ordering       = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    
    inlines = [ProfileInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display   = ['user', 'first_name', 'surname', 'is_complete', 'created_at']
    list_filter    = ['is_complete', 'created_at']
    search_fields  = ['user__email', 'first_name', 'surname']
    readonly_fields = ['created_at', 'updated_at']