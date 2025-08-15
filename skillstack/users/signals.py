from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import hashlib, hmac

from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()

@receiver(post_save, sender=User)
def ensure_profile_and_sync_email(sender, instance: User, created, **kwargs):
    profile, _ = Profile.objects.get_or_create(user=instance)
    # mirror latest email into encrypted + hash fields - KR 15/08/2025
    profile.set_encrypted_email_from_user()
    profile.save(update_fields=["email_cipher", "email_hash", "company", "bio", "profile_picture"] if not created else None)

def _email_hash_value(raw_email: str) -> str | None:
    email = (raw_email or "").strip().lower()
    salt = getattr(settings, "EMAIL_HASH_SALT", "") or ""
    if not salt:
        return None
    return hmac.new(salt.encode("utf-8"), email.encode("utf-8"), hashlib.sha256).hexdigest()

@receiver(post_save, sender=User)
def update_profile_email_hash(sender, instance, **kwargs):
    # Ensure profile exists - KR 15/08/2025
    profile, created = Profile.objects.get_or_create(user=instance)

    # Update hash if salt is set
    h = _email_hash_value(instance.email)
    if h and profile.email_hash != h:
        profile.email_hash = h
        profile.save(update_fields=["email_hash"])