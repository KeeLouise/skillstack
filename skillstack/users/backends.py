from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.conf import settings

import hashlib
import hmac

User = get_user_model()


def _email_hash_value(raw_email: str) -> str | None:
    
    email = (raw_email or "").strip().lower()
    salt = getattr(settings, "EMAIL_HASH_SALT", "") or ""
    if not salt:
        return None
    return hmac.new(salt.encode("utf-8"), email.encode("utf-8"), hashlib.sha256).hexdigest()

class EmailBackend(ModelBackend):
  
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        email_input = (username or "").strip().lower()

        # Try hashed lookup first
        try:
            from users.models import Profile 
            eh = _email_hash_value(email_input)
            if eh:
                profile = Profile.objects.select_related("user").get(email_hash=eh)
                user = profile.user
            else:
                raise Profile.DoesNotExist
        except Exception:
            
            try:
                user = User.objects.get(email__iexact=email_input)
            except User.DoesNotExist:
                return None

        # Django password + is_active checks
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None