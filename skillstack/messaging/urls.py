from django.urls import path
from .views import (
    inbox, all_messages, sent_messages, archived_messages,
    message_detail, conversation_detail, compose_message, reply_message,
    delete_message, download_attachment, api_unread_count, api_inbox_latest,
    api_mark_read, archive_message, unarchive_message
)

urlpatterns = [
    path('', inbox, name='messages'),
    path('all/', all_messages, name='all_messages'),
    path('sent/', sent_messages, name='sent'),
    path('archived/', archived_messages, name='archived_messages'),

    path('compose/', compose_message, name='compose'),
    path('<int:pk>/', message_detail, name='message_detail'),
    path('conversation/<int:pk>/', conversation_detail, name='conversation_detail'),
    path('<int:pk>/reply/', reply_message, name='reply_message'),

    path('<int:pk>/delete/', delete_message, name='delete_message'),
    path('<int:pk>/archive/', archive_message, name='archive_message'),
    path('<int:pk>/unarchive/', unarchive_message, name='unarchive_message'),

    path('attachment/<int:pk>/download/', download_attachment, name='download_attachment'),

    path('api/unread/', api_unread_count, name='api_unread_count'),
    path('api/latest/', api_inbox_latest, name='api_inbox_latest'),
    path('api/<int:pk>/mark-read/', api_mark_read, name='api_mark_read'),
]
