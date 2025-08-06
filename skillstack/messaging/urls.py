from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_messages, name='messages'),
    path('compose/', views.compose_message, name='compose'),
    path('sent/', views.sent_messages, name='sent'),  # optional
    path('<int:pk>/', views.message_detail, name='message_detail'),
]