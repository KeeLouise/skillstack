from django.db import models
from django.contrib.auth.models import User
from cloudinary_storage.storage import RawMediaCloudinaryStorage

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    project = models.ForeignKey('projects.Project', null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def last_message(self):
        return self.messages.order_by('-sent_at').first()

    def __str__(self):
        return f"Conversation({', '.join(self.participants.values_list('username', flat=True))})"


class Message(models.Model):
    IMPORTANCE_CHOICES = [('low','Low'),('normal','Normal'),('high','High')]
    conversation = models.ForeignKey(Conversation, related_name='messages',
                                     on_delete=models.CASCADE, null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=500, blank=True)
    body = models.TextField()
    importance = models.CharField(max_length=10, choices=IMPORTANCE_CHOICES, default='normal')
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    deleted_by_sender = models.BooleanField(default=False)
    deleted_by_recipient = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.sender} → {self.recipient}: {self.subject or self.body[:30]}"


class MessageAttachment(models.Model):
    message = models.ForeignKey(Message, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='message_attachments/',storage=RawMediaCloudinaryStorage())
    original_name = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    size = models.BigIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Store file size at save time (fix for file not found error) - KR 11/08/2025
        if self.file and hasattr(self.file, 'size'):
            self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return self.original_name or self.file.name