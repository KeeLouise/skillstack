from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Message, MessageAttachment, Conversation

class MessageTests(TestCase):
    def setUp(self):
        # Create users
        self.sender = User.objects.create_user(username='alice', password='testpass')
        self.recipient = User.objects.create_user(username='bob', password='testpass')

        # Create a conversation
        self.convo = Conversation.objects.create()
        self.convo.participants.add(self.sender, self.recipient)

        # Create a message
        self.message = Message.objects.create(
            conversation=self.convo,
            sender=self.sender,
            recipient=self.recipient,
            subject='Test Subject',
            body='Test Body',
            importance='normal'
        )

    def test_message_str(self):
        """Message __str__ should contain sender, recipient, and subject or body preview."""
        self.assertIn(self.sender.username, str(self.message))
        self.assertIn(self.recipient.username, str(self.message))

    def test_conversation_last_message(self):
        """Conversation.last_message should return the latest message."""
        latest = self.convo.last_message()
        self.assertEqual(latest, self.message)

    def test_create_attachment(self):
        """Should be able to attach a file to a message."""
        attachment = MessageAttachment.objects.create(
            message=self.message,
            file='message_attachments/test.txt',
            original_name='test.txt',
            size=123
        )
        self.assertEqual(attachment.message, self.message)
        self.assertEqual(attachment.original_name, 'test.txt')

    def test_inbox_view_requires_login(self):
        """Inbox view should redirect if not logged in."""
        response = self.client.get(reverse('messages'))
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_inbox_view_as_logged_in_user(self):
        """Inbox should be accessible for logged-in user."""
        self.client.login(username='alice', password='testpass')
        response = self.client.get(reverse('messages'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Messages')