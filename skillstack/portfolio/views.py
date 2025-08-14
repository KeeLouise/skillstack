from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import PortfolioLink
from .forms import PortfolioLinkForm

@login_required
def portfolio_gallery(request):
    links = PortfolioLink.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "portfolio/gallery.html", {"links": links})


@login_required
def portfolio_create(request):
    if request.method == "POST":
        form = PortfolioLinkForm(request.POST, request.FILES)
        if form.is_valid():
            link = form.save(commit=False)
            link.owner = request.user
            link.save()
            return redirect("portfolio:portfolio_gallery")
    else:
        form = PortfolioLinkForm()
    return render(request, "portfolio/create.html", {"form": form})

@login_required
def portfolio_delete(request, slug):
    link = get_object_or_404(PortfolioLink, slug=slug, owner=request.user)

    if request.method == 'POST':
        link.delete()
        messages.success(request, "Portfolio link deleted successfully.")
        return redirect('portfolio:portfolio_gallery')

    return redirect('portfolio:portfolio_gallery')

def portfolio_public(request, username):
    owner = get_object_or_404(User, username=username)
    links = PortfolioLink.objects.filter(owner=owner).order_by("-created_at")
    return render(request, "portfolio/public.html", {"owner": owner, "links": links})