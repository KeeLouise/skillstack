from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from projects.models import Project
from projects.forms import ProjectForm

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

def error_400(request, exception=None):
    return render(request, "errors/400.html", status=400)

def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)

def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)

def error_500(request):
    return render(request, "errors/500.html", status=500)

@login_required
def dashboard(request):
    user = request.user
    projects = Project.objects.filter(
        Q(owner=user) | Q(collaborators=user)
    ).distinct()

    for project in projects:
        project.my_role = "Owner" if project.owner == user else "Collaborator"

    return render(request, 'core/dashboard.html', {'projects': projects})