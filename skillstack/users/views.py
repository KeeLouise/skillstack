from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from .forms import CustomUserRegistrationForm, EmailLoginForm, UserUpdateForm, ProfileForm
from datetime import timedelta
from .models import Profile
import random

from .forms import CustomUserRegistrationForm, EmailLoginForm
from .models import EmailVerificationCode

# Register View
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user=form.save()
            #Assigns user to default group
            group, _ = Group.objects.get_or_create(name='Standard User')
            user.groups.add(group)

            messages.success(request, 'Account created! Please log in.')
            return redirect('login')
    else:
        form = CustomUserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})


# Login View
def email_login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'No account found with that email.')
                return redirect('login')

            user_auth = authenticate(request, username=user.username, password=password)
            if user_auth:
                request.session['temp_user_id'] = user.id
                send_verification_email(user)
                return redirect('verify_code')
            else:
                messages.error(request, 'Incorrect password.')
    else:
        form = EmailLoginForm()

    return render(request, 'users/login.html', {'form': form})

#Profile view
@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    is_editing = request.GET.get('edit') == 'true'

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileForm(instance=profile)
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'profile': profile,
        'is_editing': is_editing,
    }

    return render(request, 'users/profile.html', context)

# Send 2FA Verification Email
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .models import EmailVerificationCode
from django.contrib.auth import login, get_backends
import random
import logging

logger = logging.getLogger(__name__)  # for optional logging

def send_verification_email(user):
    try:
        code = str(random.randint(100000, 999999))

        EmailVerificationCode.objects.update_or_create(
            user=user,
            defaults={'code': code, 'created_at': timezone.now()}
        )

        subject = 'Your SkillStack Verification Code'
        text_body = f'Your verification code is: {code}'
        html_body = render_to_string('emails/verify_code.html', {'code': code, 'user': user, 'now': now()})

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email='email.skillstack@gmail.com',
            to=[user.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)

    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        print(f"[EMAIL ERROR] {e}")

def resend_code(request):
    user_id = request.session.get('temp_user_id')
    if not user_id:
        return redirect('login')

    user = User.objects.get(pk=user_id)
    send_verification_email(user)
    messages.success(request, 'A new verification code has been sent to your email.')
    return redirect('verify_code')

# Verify 2FA Code
def verify_2fa_code(request):
    user_id = request.session.get('temp_user_id')

    if not user_id:
        return redirect('login')

    user = User.objects.get(pk=user_id)
    code_obj = EmailVerificationCode.objects.filter(user=user).first()

    if request.method == 'POST':
        code_input = request.POST.get('code')

        # Check expiration (10 minutes)
        if code_obj and code_obj.created_at < timezone.now() - timedelta(minutes=10):
            code_obj.delete()
            messages.error(request, "Verification code expired. Please log in again.")
            return redirect('login')

        if code_obj and code_obj.code == code_input:
           backend = get_backends()[0]  # use the default backend
           user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
           login(request, user)
           request.session.pop('temp_user_id')
           code_obj.delete()
           return redirect('dashboard')
        else:
            messages.error(request, 'Invalid verification code.')

    return render(request, 'users/verify_code.html')


# Logout View
def logout_view(request):
    logout(request)
    return redirect('home')