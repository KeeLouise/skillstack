from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from projects.models import Project
from projects.forms import ProjectForm

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

@login_required
def dashboard(request):
    user = request.user
    projects = Project.objects.filter(
        Q(owner=user) | Q(collaborators=user)
    ).distinct()

    for project in projects:
        project.my_role = "Owner" if project.owner == user else "Collaborator"

    return render(request, 'core/dashboard.html', {'projects': projects})

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
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    return render(request, 'projects/project_detail.html', {'project': project})
