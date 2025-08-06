from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='messages'),
    path('sent/', views.sent_messages, name='sent'),
    path('compose/', views.compose_message, name='compose'),
    path('<int:pk>/', views.message_detail, name='message_detail'),
]