from django.urls import path
from . import views

urlpatters = [
    path('', views.inbox, name='inbox'),
    path('sent/', views.sent_messages, name='sent'),
    path ('compose/', views.compose_message, name='compose'),
    path('<int:pk>/', views.message_detail, name='message_detail'),
]