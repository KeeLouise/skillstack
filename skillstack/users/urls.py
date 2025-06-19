from django.urls import path
from .views import register_view, CustomLoginView, logout_view

urlpatterns = [
    path('register/', register_view, name='register'),
]

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
]