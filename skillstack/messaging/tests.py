from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db.models import QuerySet
import tempfile
import shutil

from .models import Conversation, Message, MessageAttachment

# Create a temporary MEDIA_ROOT for this test module - KR 14/08/2025
_TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix="test_media_")

# Force local file storage & non-manifest static storage for tests - KR 14/08/2025
# Also provide Django 5 STORAGES so nothing falls back to Cloudinary - (added after last errors) - KR 14/08/2025
_TEST_OVERRIDES = dict(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
    DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage",  # legacy fallback - KR 14/08/2025
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",  # legacy fallback - KR 14/08/2025
    MEDIA_ROOT=_TEMP_MEDIA_ROOT,
    # Makes sure any cloudinary configuration is harmless if referenced - KR 14/08/2025
    CLOUDINARY_STORAGE={
        "CLOUD_NAME": "test",
        "API_KEY": "test",
        "API_SECRET": "test",
    },
)

def _gather_context_dicts(ctx):
    """
    Normalize Django test response.context (which may be a ContextList, RequestContext,
    dict, or None) into a list of plain dicts. Robust across template backends.
    """
    dicts = []
    if ctx is None:
        return dicts

    # Plain dict case
    if isinstance(ctx, dict):
        return [ctx]

    # Context with .dicts
    if hasattr(ctx, "dicts") and isinstance(ctx.dicts, (list, tuple)):
        for d in ctx.dicts:
            if isinstance(d, dict):
                dicts.append(d)

    # ContextList is list-like
    if isinstance(ctx, (list, tuple)):
        for c in ctx:
            if isinstance(c, dict):
                dicts.append(c)
            elif hasattr(c, "dicts") and isinstance(c.dicts, (list, tuple)):
                for d in c.dicts:
                    if isinstance(d, dict):
                        dicts.append(d)

    return dicts

@override_settings(**_TEST_OVERRIDES)
class MessageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ensure MessageAttachment.file uses local FS storage even if the field was wired to Cloudinary - (added after last errors) - kr 14/08/2025
        cls._orig_storage = MessageAttachment._meta.get_field("file").storage
        MessageAttachment._meta.get_field("file").storage = FileSystemStorage(location=_TEMP_MEDIA_ROOT)

    @classmethod
    def tearDownClass(cls):
        # Restore original storage - KR 14/08/2025
        try:
            MessageAttachment._meta.get_field("file").storage = cls._orig_storage
        except Exception:
            pass
        super().tearDownClass()
        # Clean up files written to the temp MEDIA_ROOT - KR 14/08/2025
        shutil.rmtree(_TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        User = get_user_model()
        self.sender = User.objects.create_user(username="alice", password="pw")
        self.recipient = User.objects.create_user(username="bob", password="pw")

        self.convo = Conversation.objects.create()
        self.convo.participants.add(self.sender, self.recipient)

        self.message = Message.objects.create(
            conversation=self.convo,
            sender=self.sender,
            recipient=self.recipient,
            subject="Test Subject",
            body="Hello there",
            importance="normal",
        )

    # supports last_message being a property or a method - (added after further errors) - KR 14/08/2025
    def _last_message(self, convo):
        lm = convo.last_message
        return lm() if callable(lm) else lm

    def test_message_str(self):
        s = str(self.message)
        self.assertIn(self.sender.username, s)
        self.assertIn(self.recipient.username, s)
        #set subject for completeness
        self.assertTrue(("Test Subject" in s) or ("Hello there" in s))

    def test_conversation_last_message(self):
        later = Message.objects.create(
            conversation=self.convo,
            sender=self.recipient,
            recipient=self.sender,
            subject="Follow up",
            body="second",
            importance="normal",
        )
        # Handle both property and method implementations - (updated after last error) - KR 14/08/2025
        self.assertEqual(self._last_message(self.convo), later)

    def test_create_attachment(self):
        # Use local in-memory file
        uploaded = SimpleUploadedFile(
            name="hello.txt",
            content=b"hello world",
            content_type="text/plain",
        )
        attachment = MessageAttachment.objects.create(
            message=self.message,
            file=uploaded,
            size=uploaded.size,
            original_name="hello.txt",
        )
        self.assertEqual(attachment.message, self.message)
        self.assertTrue(attachment.file.name.endswith("hello.txt"))
        self.assertEqual(attachment.size, len(b"hello world"))

    def test_inbox_view_requires_login(self):
        response = self.client.get(reverse("messages"))
        self.assertEqual(response.status_code, 302)  # redirect to login - KR 14/08/2025

    def test_inbox_view_as_logged_in_user(self):
        self.client.login(username="alice", password="pw")
        response = self.client.get(reverse("messages"))
        self.assertEqual(response.status_code, 200)

        # Basic sanity check that the inbox template rendered - KR 14/08/2025
        self.assertContains(response, "Inbox")

        # Robust context check: ensure the user's conversation is present in the context
        # under any common key (conversations/threads/object_list/etc.), even with ContextList. - KR 15/08/2025
        context_dicts = _gather_context_dicts(response.context)
        candidates = []
        for d in context_dicts:
            for key in ("conversations", "threads", "items", "object_list", "inbox"):
                if key in d:
                    candidates.append(d[key])

        # scan any iterable context value that contains Conversation instances - kr 15/08/2025
        for d in context_dicts:
            for v in d.values():
                if isinstance(v, (list, tuple, QuerySet)) and any(isinstance(x, Conversation) for x in v):
                    candidates.append(v)

        flattened_ids = []
        for coll in candidates:
            try:
                flattened_ids.extend([c.id for c in coll if isinstance(c, Conversation)])
            except TypeError:
                # Not iterable; skip
                pass

        self.assertIn(
            self.convo.id,
            flattened_ids,
            msg="Inbox context should include the user's conversations (expected to find the test conversation).",
        )