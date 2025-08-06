from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_messages, name='messages'),
    path('compose/', views.compose_message, name='compose'),
    path('sent/', views.sent_messages, name='sent'), 
    path('<int:pk>/', views.message_detail, name='message_detail'),
    path('<int:pk>/reply/', views.reply_message, name='reply_message'),
    path('<int:pk>/delete/', views.delete_message, name='delete_message'),
]