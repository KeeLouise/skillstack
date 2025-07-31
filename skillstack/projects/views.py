from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from .forms import InviteCollaboratorForm, ProjectForm
from .models import Invitation, Project

import logging
logger = logging.getLogger(__name__)

def send_invite_email(email, project):
    invite_link = f"https://skillstack-1bx8.onrender.com/users/register/?email={email}&project={project.id}"
    subject = f"You’ve been invited to collaborate on {project.title}"
    body = f"""
        You've been invited to collaborate on the project "{project.title}" on SkillStack.
        
        Register or log in to accept the invitation:
        {invite_link}
    """

    email_msg = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email='email.skillstack@gmail.com',
        to=[email],
    )
    try:
        email_msg.send(fail_silently=False)
        logger.info(f"Invitation email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send invite to {email}: {e}")

@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            form.save_m2m()

            # Handles collaborator invitations - KR 31/07/2025
            invite_emails = form.cleaned_data.get('invite_emails', '')
            emails = [email.strip() for email in invite_emails.split(',') if email.strip()]

            for email in emails:
                try:
                    user = User.objects.get(email=email)
                    project.collaborators.add(user)
                    logger.info(f"Added existing user {email} as collaborator.")
                except User.DoesNotExist:
                    Invitation.objects.create(email=email, project=project, invited_by=request.user)
                    send_invite_email(email, project)

            messages.success(request, 'Project created and collaborators invited.')
            return redirect('dashboard')
    else:
        form = ProjectForm()

    return render(request, 'projects/create_project.html', {'form': form})

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user != project.owner and request.user not in project.collaborators.all():
        messages.error(request, "You do not have permission to view this project.")
        return redirect('dashboard')

    return render(request, 'projects/project_detail.html', {'project': project})