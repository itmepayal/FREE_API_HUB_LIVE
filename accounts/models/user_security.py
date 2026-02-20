import pyotp  
import hashlib
import secrets
import urllib.parse
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import BaseModel
from core.constants import LOGIN_TYPE_CHOICES, LOGIN_EMAIL_PASSWORD

class UserSecurity(BaseModel):
    # ----------------------
    # User Info
    # ----------------------
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="security"
    )
    
    # ----------------------
    # Login Type
    # ----------------------
    login_type = models.CharField(max_length=50, choices=LOGIN_TYPE_CHOICES, default=LOGIN_EMAIL_PASSWORD)

    # ----------------------
    # Authentication Tokens
    # ----------------------
    refresh_token_hash = models.CharField(max_length=64, blank=True, null=True)
    refresh_token_expiry = models.DateTimeField(blank=True, null=True)
    forgot_password_token = models.CharField(max_length=255, blank=True, null=True)
    forgot_password_expiry = models.DateTimeField(blank=True, null=True)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    email_verification_expiry = models.DateTimeField(blank=True, null=True)

    # ----------------------
    # Two-Factor Authentication (TOTP)
    # ----------------------
    is_2fa_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=32, blank=True, null=True)

    # ----------------------
    # TOTP (Two-Factor Authentication)
    # ----------------------
    def generate_totp_secret(self):
        self.totp_secret = pyotp.random_base32()
        self.save(update_fields=['totp_secret'])
        return self.totp_secret

    def get_totp_uri(self):
        issuer = urllib.parse.quote(settings.TOTP_ISSUER_NAME)
        email = urllib.parse.quote(self.user.email)
        return (
            f"otpauth://totp/{issuer}:{email}"
            f"?secret={self.totp_secret}&issuer={issuer}"
        )

    def verify_totp(self, token):
        if not self.totp_secret:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)
    
    # ----------------------
    # Refresh Token Handling
    # ----------------------
    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def generate_refresh_token(self, days=7):
        """
        Generates a refresh token, stores only its hash.
        Returns the plain token ONCE (send to client).
        """
        token = secrets.token_urlsafe(64)
        self.refresh_token_hash = self._hash_token(token)
        self.refresh_token_expiry = timezone.now() + timedelta(days=days)
        
        self.save(update_fields=["refresh_token_hash", "refresh_token_expiry"])
        return token 

    def verify_refresh_token(self, token: str) -> bool:
        """
        Verifies provided refresh token.
        """
        if not self.refresh_token_hash or not self.refresh_token_expiry:
            return False

        if timezone.now() > self.refresh_token_expiry:
            return False

        return self._hash_token(token) == self.refresh_token_hash

    def revoke_refresh_token(self):
        """
        Logout / token rotation
        """
        self.refresh_token_hash = None
        self.refresh_token_expiry = None
        self.save(update_fields=["refresh_token_hash", "refresh_token_expiry"])
        
    # ----------------------
    # String Representation
    # ----------------------
    def __str__(self):
        return f"Security<{self.user.email}>"
