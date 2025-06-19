from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from projects.models import Project

def home(request):
    return render(request, 'home.html')

@login_required
def dashboard(request):
    user_projects = Project.objects.filter(owner=request.user)
    return render(request, 'core/dashboard.html', {'projects': user_projects})
