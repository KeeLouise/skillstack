from django.core.mail import EmailMultiAlternatives, send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.http import FileResponse, Http404

from .forms import InviteCollaboratorForm, ProjectForm
from .forms import ProjectAttachmentUploadForm
from .models import Invitation, Project, ProjectAttachment

import logging
logger = logging.getLogger(__name__)


# Sends email invitation for users who don’t yet have accounts – KR 31/07/2025
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


# Notifies existing users by email when added as collaborators – KR 31/07/2025
def notify_existing_collaborator(user, project):
    send_mail(
        subject='You have been added to a new project on Skillstack',
        message=f'Hello {user.first_name or user.username},\n\n'
                f'You’ve been added as a collaborator to the project: "{project.title}". '
                f'You can view it now in your dashboard.',
        from_email='email.skillstack@gmail.com',
        recipient_list=[user.email],
        fail_silently=False,
    )


@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            form.save_m2m()

            files = request.FILES.getlist('attachments')
            for f in files:
                if not f:
                    continue
                ProjectAttachment.objects.create(
                    project=project,
                    file=f,
                    original_name=getattr(f, 'name', '') or '',
                    size=getattr(f, 'size', None),
                )

            # Invite collaborators (existing users get added; non-users get invitations) - KR 12/08/2025
            invite_emails = form.cleaned_data.get('invite_emails', '')
            emails = [e.strip() for e in invite_emails.split(',') if e.strip()]
            for email in emails:
                try:
                    user = User.objects.get(email=email)
                    project.collaborators.add(user)
                    notify_existing_collaborator(user, project)
                except User.DoesNotExist:
                    Invitation.objects.create(email=email, project=project, invited_by=request.user)
                    send_invite_email(email, project)

            messages.success(request, 'Project created and any collaborators included have been invited.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectForm()

    return render(request, 'projects/create_project.html', {'form': form})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if not (
        request.user == project.owner
        or project.collaborators.filter(pk=request.user.pk).exists()
    ):
        messages.error(request, "You do not have permission to view this project.")
        return redirect('dashboard')

    upload_form = ProjectAttachmentUploadForm()
    attachments = project.attachments.select_related('uploaded_by').all()
    can_upload = (request.user == project.owner) or project.collaborators.filter(pk=request.user.pk).exists()

    return render(request, 'projects/project_detail.html', {
        'project': project,
        'upload_form': upload_form,
        'attachments': attachments,
        'can_upload': can_upload,
})


@login_required
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user != project.owner:
        messages.error(request, "You don't have permission to edit this project.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            with transaction.atomic():
                form.save()

                files = request.FILES.getlist('attachments')
                for f in files:
                    if not f:
                        continue
                    kwargs = {
                        'project': project,
                        'file': f,
                        'original_name': getattr(f, 'name', '') or '',
                        'size': getattr(f, 'size', None),
                    }
                    if hasattr(ProjectAttachment, 'uploaded_by'):
                        kwargs['uploaded_by'] = request.user
                    ProjectAttachment.objects.create(**kwargs)

            messages.success(request, 'Project updated successfully.')
            return redirect('project_detail', pk=project.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectForm(instance=project)

    return render(request, 'projects/edit_project.html', {'form': form, 'project': project})


@login_required
@require_POST
def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user != project.owner:
        messages.error(request, "You don't have permission to delete this project.")
        return redirect('dashboard')

    project.delete()
    messages.success(request, "Project deleted successfully.")
    return redirect('dashboard')


@login_required
@require_POST
def upload_project_attachments(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if not (request.user == project.owner or project.collaborators.filter(pk=request.user.pk).exists()):
        messages.error(request, "You don't have permission to upload files to this project.")
        return redirect('project_detail', pk=project.pk)

    form = ProjectAttachmentUploadForm(request.POST, request.FILES)

    files = request.FILES.getlist('files')
    if not files:
        messages.error(request, "Please choose at least one file.")
        return redirect('project_detail', pk=project.pk)

    created = 0
    with transaction.atomic():
        for f in files:
            if not f:
                continue
            ProjectAttachment.objects.create(
                project=project,
                file=f,
                original_name=getattr(f, 'name', '') or '',
                size=getattr(f, 'size', None),
                uploaded_by=request.user,
            )
            created += 1

    if created:
        messages.success(request, f"Uploaded {created} file{'s' if created != 1 else ''}.")
    else:
        messages.info(request, "No files were uploaded.")
    return redirect('project_detail', pk=project.pk)


@login_required
def download_project_attachment(request, att_pk):
    att = get_object_or_404(
        ProjectAttachment.objects.select_related('project', 'uploaded_by'),
        pk=att_pk
    )
    project = att.project

    if request.user != project.owner and request.user not in project.collaborators.all():
        raise Http404("Not found")

    if not att.file:
        raise Http404("File not available")

    try:
        f = att.file.open('rb')
    except Exception:
        raise Http404("File not available")

    filename = att.original_name or att.file.name
    return FileResponse(f, as_attachment=True, filename=filename)


@login_required
@require_POST
def delete_project_attachment(request, att_pk):
    att = get_object_or_404(
        ProjectAttachment.objects.select_related('project', 'uploaded_by'),
        pk=att_pk
    )
    project = att.project

    if request.user != project.owner and request.user != att.uploaded_by:
        messages.error(request, "You don't have permission to delete this attachment.")
        return redirect('project_detail', pk=project.pk)

    att.delete()
    messages.success(request, "Attachment deleted.")
    return redirect('project_detail', pk=project.pk)