from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    register_view, email_login_view, logout_view,
    verify_2fa_code, resend_code, profile_view, edit_profile_view, collaborator_profile_view, check_username
)

app_name = "users" 

urlpatterns = [
    path('register/', register_view, name='register'),
    path("check-username/", check_username, name="check_username"),
    path('login/', email_login_view, name='login'),
    path("profile/", profile_view, name="profile"),
    path("profile/edit/", edit_profile_view, name="edit_profile"),
    path('logout/', logout_view, name='logout'),
    path('verify/', verify_2fa_code, name='verify_code'),
    path('resend/', resend_code, name='resend_code'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),

    # Collaborator-only profile 
    path("c/<int:user_id>/", collaborator_profile_view, name="collab_profile"),
]