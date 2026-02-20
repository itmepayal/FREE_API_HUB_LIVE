from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from accounts.models.user_security import UserSecurity
from accounts.models.user_presence import UserPresence

# =====================================================
# Inline Admins
# =====================================================

class UserSecurityInline(admin.StackedInline):
    model = UserSecurity
    can_delete = False
    extra = 0
    readonly_fields = (
        "masked_refresh_token",
        "forgot_password_token",
        "forgot_password_expiry",
        "email_verification_token",
        "email_verification_expiry",
        "totp_secret",
    )

    def masked_refresh_token(self, obj):
        """Display first 6 chars of refresh token hash (safe)."""
        if obj.refresh_token_hash:
            return f"{obj.refresh_token_hash[:6]}..."  
        return "-"
    masked_refresh_token.short_description = "Refresh Token"

class UserPresenceInline(admin.StackedInline):
    model = UserPresence
    can_delete = False
    extra = 0
    readonly_fields = ("last_seen",)


# =====================================================
# User Admin
# =====================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    
    # -------------------------
    # Custom List Columns
    # -------------------------
    def is_online(self, obj):
        return getattr(obj.presence, "is_online", False)
    is_online.boolean = True
    is_online.short_description = "Online"

    def two_factor(self, obj):
        return getattr(obj.security, "is_2fa_enabled", False)
    two_factor.boolean = True
    two_factor.short_description = "2FA"

    # List Page
    list_display = (
        "email",
        "username",
        "role",
        "is_verified",
        "is_online",
        "two_factor",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "is_verified",
        "is_staff",
        "is_active",
    )

    search_fields = ("email", "username")
    ordering = ("email",)

    # Detail Page
    fieldsets = (
        (None, {"fields": ("email", "username", "password", "avatar")}),
        (_("Permissions"), {
            "fields": (
                "role",
                "is_verified",
                "is_staff",
                "is_superuser",
                "is_active",
                "groups",
                "user_permissions",
            )
        }),
        (_("Important dates"), {"fields": ("last_login",)}),
    )

    # Create User Page
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "username",
                "password1",
                "password2",
                "role",
                "is_staff",
                "is_verified",
            ),
        }),
    )

    # Inlines
    inlines = (UserSecurityInline, UserPresenceInline)

    # Read-only
    readonly_fields = ("last_login",)

    # Django auth config
    filter_horizontal = ("groups", "user_permissions")
