from django.urls import path
from .views import (
    register_view, email_login_view, logout_view,
    verify_2fa_code, resend_code,
)

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', email_login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('verify/', verify_2fa_code, name='verify_code'),
    path('resend/', resend_code, name='resend_code'),
]