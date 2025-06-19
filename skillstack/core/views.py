from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from projects.models import Project
from projects.forms import ProjectForm

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

@login_required
def dashboard(request):
    user_projects = Project.objects.filter(owner=request.user)
    return render(request, 'core/dashboard.html', {'projects': user_projects})

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
