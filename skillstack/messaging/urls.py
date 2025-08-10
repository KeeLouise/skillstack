from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='messages'),                  # Inbox
    path('all/', views.all_messages, name='all_messages'),   # All Messages
    path('sent/', views.sent_messages, name='sent'),         # Sent
    path('compose/', views.compose_message, name='compose'), # Compose
    path('<int:pk>/', views.message_detail, name='message_detail'), # Message Detail
    path('<int:pk>/reply/', views.reply_message, name='reply_message'), # Message Replies
    path('<int:pk>/delete/', views.delete_message, name='delete_message'), # Delete Message
    path('conversations/<int:pk>/', views.conversation_detail, name='conversation_detail'), # Conversation Detail

     # --- NEW JSON API endpoints ---
    path('api/unread-count/', views.api_unread_count, name='api_unread_count'),
    path('api/inbox-latest/', views.api_inbox_latest, name='api_inbox_latest'),
    path('api/mark-read/<int:pk>/', views.api_mark_read, name='api_mark_read'),
]
