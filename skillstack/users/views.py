from django.shortcuts import render, redirect, get_object_or_404
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
from django.db.models import Q

from .forms import CustomUserRegistrationForm, EmailLoginForm
from .models import EmailVerificationCode
from projects.models import Project, Invitation

# Register View
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    # This will check if the user was invited - KR 31/07/2025
    email = request.GET.get('email')
    project_id = request.GET.get('project')

    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # This assigns the user to the "Standard User" group - KR 31/07/2025
            group, _ = Group.objects.get_or_create(name='Standard User')
            user.groups.add(group)

            # If the user was invited to a projected, it will add this project to their dashboard - KR 31/07/2025
            if email and project_id:
                try:
                    project = Project.objects.get(id=project_id)
                    if project:
                        project.collaborators.add(user)
                        Invitation.objects.filter(email=user.email, project=project).update(accepted=True)
                except Project.DoesNotExist:
                    pass 

            messages.success(request, 'Account created! Please log in.')
            return redirect('login')
    else:
        form = CustomUserRegistrationForm(initial={'email': email} if email else None)

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

@login_required
def profile_view(request):
    """Read-only profile page with recent projects."""
    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Calculate profile completeness - KR 12/08/2025
    fields_to_check = [
        request.user.first_name,
        request.user.email,
        profile.company,
        profile.bio,
        profile.profile_picture
    ]
    filled_fields = sum(1 for field in fields_to_check if field)
    completeness_percentage = int((filled_fields / len(fields_to_check)) * 100)

    # Recent projects ordering logic - KR 12/08/2025
    order_fields = []
    if hasattr(Project, "updated_at"):
        order_fields.append("-updated_at")
    if hasattr(Project, "created_at"):
        order_fields.append("-created_at")
    if not order_fields:
        order_fields = ["-id"]

    project_list = (
        Project.objects
        .filter(Q(owner=request.user) | Q(collaborators=request.user))
        .select_related("owner")
        .prefetch_related("collaborators")
        .order_by(*order_fields)[:4]
    )

    return render(
        request,
        "users/profile.html",
        {
            "profile": profile,
            "project_list": project_list,
            "completeness_percentage": completeness_percentage,
        },
    )

@login_required
def edit_profile_view(request):
    """Edit form page (uses users/edit_profile.html)."""
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("profile")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileForm(instance=profile)

    return render(
        request,
        "users/edit_profile.html",
        {"u_form": u_form, "p_form": p_form, "profile": profile},
    )

# users/views.py

@login_required
def collaborator_profile_view(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    profile, _ = Profile.objects.get_or_create(user=target)

    if target == request.user:
        return redirect("profile")

    # Check access: must share at least one project – KR 13/08/2025
    owner_is_target = Project.objects.filter(owner=target, collaborators=request.user)
    owner_is_me = Project.objects.filter(owner=request.user, collaborators=target)
    both_collabs = Project.objects.filter(collaborators=target).filter(collaborators=request.user)
    has_shared_project = owner_is_target.exists() or owner_is_me.exists() or both_collabs.exists()

    if not has_shared_project:
        messages.error(request, "You can only view profiles of collaborators you share a project with.")
        return redirect("dashboard")

    # Recent projects *LIMITED TO SHARED BETWEEN* request.user and target – KR 13/08/2025
    shared_q = (
        Q(owner=target) | Q(collaborators=target)
    ) & (
        Q(owner=request.user) | Q(collaborators=request.user)
    )

    order_fields = []
    if hasattr(Project, "updated_at"):
        order_fields.append("-updated_at")
    if hasattr(Project, "created_at"):
        order_fields.append("-created_at")
    if not order_fields:
        order_fields = ["-id"]

    project_list = (
        Project.objects
        .filter(shared_q)
        .select_related("owner")
        .prefetch_related("collaborators")
        .distinct()
        .order_by(*order_fields)[:6]
    )

    return render(
        request,
        "users/profile_collab.html",
        {
            "viewed_user": target,
            "profile": profile,
            "project_list": project_list,
        },
    )

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