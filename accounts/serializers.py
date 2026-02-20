from urllib.parse import quote

from django.conf import settings
from rest_framework import serializers

from accounts.models import User, UserPresence, UserSecurity
from core.constants import ROLE_CHOICES

# ----------------------------
# Nested Serializers for Related Models
# ----------------------------
class UserPresenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPresence
        fields = ["is_online", "last_seen", "status_message"]
        read_only_fields = ["is_online", "last_seen", "status_message"]

class UserSecuritySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSecurity
        fields = ["is_2fa_enabled"]
        read_only_fields = ["is_2fa_enabled"]

# ----------------------------
# User Serializer (Main)
# ----------------------------
class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField(help_text="Full URL to user's avatar")
    presence = UserPresenceSerializer(read_only=True)
    security = UserSecuritySerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "role",
            "is_verified",
            "avatar_url",
            "presence",
            "security",
        ]
        read_only_fields = ["id", "avatar_url", "presence", "security"]

    def get_avatar_url(self, obj):
        """Return full URL for avatar or fallback to UI Avatar."""
        return obj.avatar_url  
    
# ----------------------------
# Register Serializer
# ----------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["email", "username", "password"]

    def create(self, validated_data):
        """Create a new user with hashed password."""
        user = User(
            email=validated_data["email"],
            username=validated_data["username"]
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

# ----------------------------
# Verify Email Serializer
# ----------------------------
class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="Email verification token")

# ----------------------------
# Login Serializer
# ----------------------------
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="User email for login")
    password = serializers.CharField(write_only=True, help_text="User password")
    token = serializers.CharField(
        write_only=True, required=False, allow_blank=True, default=""
    )

# ----------------------------
# Forgot Password Serializer
# ----------------------------
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email to send reset password link")

# ----------------------------
# Reset Password Serializer
# ----------------------------
class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="Password reset token")
    new_password = serializers.CharField(
        write_only=True, min_length=6, help_text="New password to set"
    )

# ----------------------------
# Change Password Serializer
# ----------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, help_text="Current password")
    new_password = serializers.CharField(write_only=True, min_length=6, help_text="New password")

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})
        return attrs
    
# ----------------------------
# Resend Email Verification Serializer
# ----------------------------
class ResendEmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email to resend verification")

    def validate_email(self, value):
        """Ensure the email exists and is not already verified."""
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No account found with this email.")

        if user.is_verified:
            raise serializers.ValidationError("This email is already verified.")

        self.context["user"] = user
        return value

    def validate(self, attrs):
        """Attach user to validated data."""
        attrs["user"] = self.context["user"]
        return attrs

# ----------------------------
# Avatar Serializer
# ----------------------------
class UpdateAvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=True, allow_null=False, help_text="Upload new avatar image")
    
    class Meta:
        model = User
        fields = ["avatar"]

# ----------------------------
# Role Serializer
# ----------------------------
class ChangeRoleSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=True, help_text="User ID to change role")
    role = serializers.ChoiceField(choices=ROLE_CHOICES, required=True, help_text="New role")

# ----------------------------
# OAuth Callback
# ----------------------------
class OAuthCallbackSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, help_text="OAuth authorization code")

# ----------------------------
# Empty Serializer
# ----------------------------
class EmptySerializer(serializers.Serializer):
    pass

# ----------------------------
# Refresh Token
# ----------------------------
class RefreshTokenInputSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True, help_text="Refresh token string")

# ----------------------------
# Enable 2FA Serializer
# ----------------------------
class Enable2FASerializer(serializers.Serializer):
    token = serializers.CharField(
        required=True,
        write_only=True,
        help_text="TOTP token generated by authenticator app to enable 2FA",
    )

# ----------------------------
# Disable 2FA Serializer
# ----------------------------
class Disable2FASerializer(serializers.Serializer):
    token = serializers.CharField(
        required=True,
        write_only=True,
        help_text="TOTP token to confirm disabling 2FA",
    )

# ----------------------------
# Setup 2FA Serializer
# ----------------------------
class Setup2FASerializer(serializers.Serializer):
    totp_uri = serializers.CharField(read_only=True, help_text="TOTP URI for authenticator app")
    qr_code = serializers.CharField(read_only=True, help_text="Base64 QR code for scanning")
    