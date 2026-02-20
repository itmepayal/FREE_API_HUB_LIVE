from urllib.parse import quote

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from accounts.managers import UserManager

from core.models import BaseModel
from core.constants import ROLE_CHOICES, ROLE_USER

class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    # ----------------------
    # Basic User Info
    # ----------------------
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, db_index=True)
    avatar = models.URLField(blank=True, null=True)

    # ----------------------
    # Role 
    # ----------------------
    role = models.CharField(
        max_length=50, 
        choices=ROLE_CHOICES, 
        default=ROLE_USER
    )

    # ----------------------
    # Account Status Flags
    # ----------------------
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # ----------------------
    # User Model Config
    # ----------------------
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    # ----------------------
    # Avatar URL
    # ----------------------
    @property
    def avatar_url(self):
        if self.avatar and self.avatar.startswith("http"):
            return self.avatar
        return f"https://ui-avatars.com/api/?name={quote(self.username)}&size=200"

    # ----------------------
    # String Representation
    # ----------------------
    def __str__(self):
        return self.email
    