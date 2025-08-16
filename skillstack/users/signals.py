from django.contrib.auth.models import User
from django.db.models.signals import post_save         
from django.dispatch import receiver                     
from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Ensure related Profile data gets saved whenever the User saves - KR 15/08/2025
        instance.profile.save()

@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    """
    Make sure every User has a Profile.
    Works for newly created users and for existing users saved again.
    """
    Profile.objects.get_or_create(user=instance)