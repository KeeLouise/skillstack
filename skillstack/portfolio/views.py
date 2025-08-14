from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from .models import PortfolioLink
from .forms import PortfolioLinkForm

@login_required
def portfolio_gallery(request):
    links = PortfolioLink.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'portfolio/gallery.html', {'links': links})

@login_required
def portfolio_create(request):
    if request.method == 'POST':
        form = PortfolioLinkForm(request.POST, request.FILES)
        if form.is_valid():
            link = form.save(commit=False)
            link.owner = request.user
            link.save()
            return redirect('portfolio_dashboard')
    else:
        form = PortfolioLinkForm()
    return render(request, 'portfolio/create.html', {'form': form})

def portfolio_public(request, username):
    owner = get_object_or_404(User, username=username)
    links = PortfolioLink.objects.filter(owner=owner, is_published=True).order_by('-created_at')
    return render(request, 'portfolio/public.html', {'owner': owner, 'links': links})