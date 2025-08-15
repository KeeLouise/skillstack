from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django_cryptography.fields import encrypt
import hashlib, hmac



def email_hash_value(email: str) -> str:
    email = (email or "").strip().lower()
    key = (getattr(settings, "EMAIL_HASH_SALT", "") or "").encode("utf-8")
    return hmac.new(key, email.encode("utf-8"), hashlib.sha256).hexdigest()


class EmailVerificationCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.code}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)

    email_cipher = encrypt(models.TextField(blank=True, null=True))
    # Deterministic salted hash for uniqueness / indexing without revealing the email - KR 15/08/2025
    email_hash = models.CharField(max_length=64, blank=True, null=True, unique=True, db_index=True)

    # Mirror helper used wherever you update User.email - KR 15/08/2025
    def set_encrypted_email_from_user(self):
        raw_email = (self.user.email or "").strip()
        self.email_cipher = raw_email or None
        self.email_hash = email_hash_value(raw_email) if raw_email else None

    def save(self, *args, **kwargs):
        # Keep hash/cipher in sync if user.email changed or fields are empty - KR 15/08/2025
        if not self.email_cipher or not self.email_hash:
            self.set_encrypted_email_from_user()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s Profile"