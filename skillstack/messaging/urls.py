from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_messages, name='messages'),
    path('compose/', views.compose_message, name='compose'),
    path('<int:pk>/', views.message_detail, name='message_detail'),
]