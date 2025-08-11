from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from unittest.mock import patch
from .models import Profile, EmailVerificationCode
from .forms import CustomUserRegistrationForm, EmailLoginForm
from django.utils import timezone
from datetime import timedelta

class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="password123",
            email="test@example.com"
        )
        self.profile = Profile.objects.create(user=self.user, company="Test Co")

    def test_profile_str(self):
        self.assertEqual(str(self.profile), "testuser's Profile")

    def test_email_verification_code_str(self):
        code = EmailVerificationCode.objects.create(user=self.user, code="123456")
        self.assertEqual(str(code), "testuser - 123456")


class UserFormTests(TestCase):
    def test_registration_form_valid(self):
        form_data = {
            'username': 'newuser',
            'full_name': 'New User',
            'email': 'new@example.com',
            'company': 'Test Co',
            'password1': 'ComplexPass123',
            'password2': 'ComplexPass123',
        }
        form = CustomUserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_email_login_form_invalid_password(self):
        user = User.objects.create_user(username="u1", email="e1@example.com", password="pass123")
        form = EmailLoginForm(data={'email': 'e1@example.com', 'password': 'wrongpass'})
        self.assertFalse(form.is_valid())


class UserViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_password = "password123"
        self.user = User.objects.create_user(
            username="testuser",
            password=self.user_password,
            email="test@example.com"
        )
        Profile.objects.create(user=self.user, company="Test Co")

    def test_register_view_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    @patch('users.views.send_verification_email')
    def test_email_login_view_valid(self, mock_send_email):
        response = self.client.post(reverse('login'), {
            'email': 'test@example.com',
            'password': self.user_password
        })
        self.assertEqual(response.status_code, 302)  # redirect to verify_code
        mock_send_email.assert_called_once()

    def test_profile_view_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_profile_view_post_update(self):
        self.client.login(username="testuser", password=self.user_password)
        response = self.client.post(reverse('profile'), {
            'first_name': 'Updated Name',
            'email': 'updated@example.com',
            'company': 'Updated Co',
            'bio': 'Updated bio'
        })
        self.assertEqual(response.status_code, 302)  # redirect after update
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated Name')

    def test_verify_2fa_code_success(self):
        EmailVerificationCode.objects.create(user=self.user, code="123456", created_at=timezone.now())
        session = self.client.session
        session['temp_user_id'] = self.user.id
        session.save()
        response = self.client.post(reverse('verify_code'), {'code': '123456'})
        self.assertEqual(response.status_code, 302)  # redirect to dashboard

    def test_verify_2fa_code_expired(self):
        session = self.client.session
        session['temp_user_id'] = self.user.id
        session.save()

    # First create normally so auto_now_add sets created_at
        code_obj = EmailVerificationCode.objects.create(
            user=self.user,
            code="123456"
    )

    # Now manually update the created_at in the DB to force expiry
        EmailVerificationCode.objects.filter(pk=code_obj.pk).update(
        created_at=timezone.now() - timedelta(days=1)
    )

        response = self.client.post(reverse('verify_code'), {'code': '123456'})

        self.assertRedirects(response, reverse('login'))
        self.assertFalse(EmailVerificationCode.objects.filter(user=self.user).exists())