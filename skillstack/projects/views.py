from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import InviteCollaboratorForm, ProjectForm
from .models import Invitation, Project
from django.urls import reverse

@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            return redirect('dashboard')
    else:
        form = ProjectForm()
    return render(request, 'projects/create_project.html', {'form': form})

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    return render(request, 'projects/project_detail.html', {'project': project})

@login_required
def invite_collaborator(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)

    if request.method == 'POST':
        form = InviteCollaboratorForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # This will check if the user exists on database - KR 31/07/2025
            try:
                user = User.objects.get(email=email)
                project.collaborators.add(user)
            except User.DoesNotExist:
                # If the user does not exist, they will be sent an invitation email - KR 31/07/2025
                Invitation.objects.create(email=email, project=project, invited_by=request.user)
                invite_link = request.build_absolute_uri(
                    reverse('register') + f'?email={email}&project={project.id}'
                )
                send_mail(
                    subject='You’ve been invited to collaborate on a project on Skillstack',
                    message=f'You’ve been invited to join the project "{project.title}". Register here: {invite_link}',
                    from_email='email.skillstack@gmail.com',
                    recipient_list=[email],
                    fail_silently=False,
                )

            return redirect('project_detail', project_id=project.id)
    else:
        form = InviteCollaboratorForm()

    return render(request, 'projects/invite_collaborator.html', {'form': form, 'project': project})