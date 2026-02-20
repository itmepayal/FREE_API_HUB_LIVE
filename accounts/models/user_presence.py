from django.db import models
from django.utils import timezone

from core.models import BaseModel

class UserPresence(BaseModel):
    # ----------------------
    # User Info
    # ----------------------
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="presence"
    )
    
    # ----------------------
    # Realtime Presence 
    # ----------------------
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(blank=True, null=True)
    status_message = models.CharField(max_length=255, blank=True, null=True, default="Hey there! I am using config Hub.")
    
    # ----------------------
    # Online Presence Helpers
    # ----------------------
    def mark_online(self):
        self.is_online = True
        self.last_seen = timezone.now()
        self.save(update_fields=["is_online", "last_seen"])

    def mark_offline(self):
        self.is_online = False
        self.last_seen = timezone.now()
        self.save(update_fields=["is_online", "last_seen"])

    # ----------------------
    # String Representation
    # ----------------------
    def __str__(self):
        return f"Presence<{self.user.email}>"

