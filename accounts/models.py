import pyotp
import hashlib
import secrets
import urllib.parse
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from urllib.parse import quote

from accounts.managers import UserManager
from core.models import BaseModel
from core.constants import (
    ROLE_CHOICES,
    ROLE_USER,
    LOGIN_TYPE_CHOICES,
    LOGIN_EMAIL_PASSWORD,
)


class User(BaseModel, AbstractBaseUser, PermissionsMixin):

    # =====================================================
    # BASIC USER INFO
    # =====================================================
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, db_index=True)
    avatar = models.URLField(blank=True, null=True)

    # =====================================================
    # ROLE
    # =====================================================
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default=ROLE_USER
    )

    # =====================================================
    # ACCOUNT STATUS
    # =====================================================
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # =====================================================
    # LOGIN TYPE
    # =====================================================
    login_type = models.CharField(
        max_length=50,
        choices=LOGIN_TYPE_CHOICES,
        default=LOGIN_EMAIL_PASSWORD
    )

    # =====================================================
    # TOKEN MANAGEMENT
    # =====================================================
    refresh_token_hash = models.CharField(max_length=64, blank=True, null=True)
    refresh_token_expiry = models.DateTimeField(blank=True, null=True)

    forgot_password_token = models.CharField(max_length=255, blank=True, null=True)
    forgot_password_expiry = models.DateTimeField(blank=True, null=True)

    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    email_verification_expiry = models.DateTimeField(blank=True, null=True)

    # =====================================================
    # TWO FACTOR AUTHENTICATION (TOTP)
    # =====================================================
    is_2fa_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=32, blank=True, null=True)

    # =====================================================
    # REALTIME PRESENCE
    # =====================================================
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(blank=True, null=True)
    status_message = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default="Hey there! I am using config Hub."
    )

    # =====================================================
    # DJANGO CONFIG
    # =====================================================
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    # =====================================================
    # AVATAR HELPER
    # =====================================================
    @property
    def avatar_url(self):
        if self.avatar and self.avatar.startswith("http"):
            return self.avatar
        return f"https://ui-avatars.com/api/?name={quote(self.username)}&size=200"

    # =====================================================
    # 2FA METHODS
    # =====================================================
    def generate_totp_secret(self):
        self.totp_secret = pyotp.random_base32()
        self.save(update_fields=["totp_secret"])
        return self.totp_secret

    def get_totp_uri(self):
        issuer = urllib.parse.quote(settings.TOTP_ISSUER_NAME)
        email = urllib.parse.quote(self.email)
        return (
            f"otpauth://totp/{issuer}:{email}"
            f"?secret={self.totp_secret}&issuer={issuer}"
        )

    def verify_totp(self, token):
        if not self.totp_secret:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)

    # =====================================================
    # TOKEN HELPERS
    # =====================================================
    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def generate_refresh_token(self, days=7):
        token = secrets.token_urlsafe(64)
        self.refresh_token_hash = self._hash_token(token)
        self.refresh_token_expiry = timezone.now() + timedelta(days=days)

        self.save(update_fields=["refresh_token_hash", "refresh_token_expiry"])
        return token

    def verify_refresh_token(self, token: str) -> bool:
        if not self.refresh_token_hash or not self.refresh_token_expiry:
            return False

        if timezone.now() > self.refresh_token_expiry:
            return False

        return self._hash_token(token) == self.refresh_token_hash

    def revoke_refresh_token(self):
        self.refresh_token_hash = None
        self.refresh_token_expiry = None
        self.save(update_fields=["refresh_token_hash", "refresh_token_expiry"])

    # =====================================================
    # PRESENCE HELPERS
    # =====================================================
    def mark_online(self):
        self.is_online = True
        self.last_seen = timezone.now()
        self.save(update_fields=["is_online", "last_seen"])

    def mark_offline(self):
        self.is_online = False
        self.last_seen = timezone.now()
        self.save(update_fields=["is_online", "last_seen"])

    # =====================================================
    # STRING REPRESENTATION
    # =====================================================
    def __str__(self):
        return self.email