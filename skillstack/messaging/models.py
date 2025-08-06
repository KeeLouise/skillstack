from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    IMPORTANCE_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=500)
    body = models.TextField()
    importance = models.CharField(max_length=10, choices=IMPORTANCE_CHOICES, default='normal')
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"From {self.sender} to {self.recipient} - {self.subject}"
