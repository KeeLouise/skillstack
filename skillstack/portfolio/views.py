from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import PortfolioLink
from .forms import PortfolioLinkForm
from django.templatetags.static import static

def _display_image_abs(request, link: PortfolioLink) -> str:
    """
    Returns an absolute URL for the link's preview image.
    - Prefers uploaded file, falls back to image_url.
    - If relative, makes it absolute.
    - If nothing is available, returns a default static image.
    """
    img = None
    try:
        if getattr(link, "image_file", None):
            if getattr(link.image_file, "url", None):
                img = link.image_file.url
    except Exception:
        img = None

    if not img:
        img = link.image_url

    if img:
        if img.startswith("http://") or img.startswith("https://"):
            return img
        return request.build_absolute_uri(img)

    return request.build_absolute_uri(static("images/og/portfolio-default.jpg"))


@login_required
def portfolio_gallery(request):
    links = PortfolioLink.objects.filter(owner=request.user).order_by("-created_at")
    for l in links:
        l.display_image = _display_image_abs(request, l)

    og_image = links[0].display_image if links else request.build_absolute_uri(
        static("images/og/portfolio-default.jpg")
    )

    return render(
        request,
        "portfolio/gallery.html",
        {"links": links, "og_image": og_image},
    )


@login_required
def portfolio_create(request):
    if request.method == "POST":
        form = PortfolioLinkForm(request.POST, request.FILES)
        if form.is_valid():
            link = form.save(commit=False)
            link.owner = request.user
            link.save()
            link.ensure_preview()
            messages.success(request, "Link added to your portfolio.")
            return redirect("portfolio:portfolio_gallery")
    else:
        form = PortfolioLinkForm()
    return render(request, "portfolio/create.html", {"form": form})


def portfolio_public(request, username):
    owner = get_object_or_404(User, username=username)
    links = PortfolioLink.objects.filter(owner=owner, is_published=True).order_by("-created_at")

    for l in links:
        l.display_image = _display_image_abs(request, l)

    og_image = links[0].display_image if links else request.build_absolute_uri(
        static("images/og/portfolio-default.jpg")
    )

    return render(
        request,
        "portfolio/public.html",
        {"owner": owner, "links": links, "og_image": og_image},
    )

@login_required
def portfolio_delete(request, slug):
    link = get_object_or_404(PortfolioLink, slug=slug, owner=request.user)

    if request.method == 'POST':
        link.delete()
        messages.success(request, "Portfolio link deleted successfully.")
        return redirect('portfolio:portfolio_gallery')

    return redirect('portfolio:portfolio_gallery')
