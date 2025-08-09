from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='messages'),                  # Inbox
    path('all/', views.all_messages, name='all_messages'),   # All Messages
    path('sent/', views.sent_messages, name='sent'),         # Sent
    path('compose/', views.compose_message, name='compose'), # Compose
    path('<int:pk>/', views.message_detail, name='message_detail'),
    path('<int:pk>/reply/', views.reply_message, name='reply_message'),
    path('<int:pk>/delete/', views.delete_message, name='delete_message'),
    path('conversations/<int:pk>/', views.conversation_detail, name='conversation_detail')
]
