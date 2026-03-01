from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    # =====================================================
    # LIST PAGE
    # =====================================================

    list_display = (
        "email",
        "username",
        "role",
        "is_verified",
        "is_online",
        "is_2fa_enabled",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "is_verified",
        "is_online",
        "is_2fa_enabled",
        "is_staff",
        "is_active",
    )

    search_fields = ("email", "username")
    ordering = ("email",)

    # =====================================================
    # DETAIL PAGE
    # =====================================================

    fieldsets = (
        (None, {
            "fields": ("email", "username", "password", "avatar")
        }),

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

        (_("Security"), {
            "fields": (
                "login_type",
                "is_2fa_enabled",
                "totp_secret",
                "refresh_token_hash",
                "refresh_token_expiry",
                "forgot_password_token",
                "forgot_password_expiry",
                "email_verification_token",
                "email_verification_expiry",
            )
        }),

        (_("Presence"), {
            "fields": (
                "is_online",
                "last_seen",
                "status_message",
            )
        }),

        (_("Important dates"), {
            "fields": ("last_login",)
        }),
    )

    # =====================================================
    # CREATE USER PAGE
    # =====================================================

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
                "is_active",
            ),
        }),
    )

    readonly_fields = (
        "last_login",
        "refresh_token_hash",
        "refresh_token_expiry",
        "forgot_password_expiry",
        "email_verification_expiry",
        "last_seen",
    )

    filter_horizontal = ("groups", "user_permissions")