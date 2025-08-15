from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest
from django.templatetags.static import static
from django.contrib.staticfiles.storage import staticfiles_storage

from .models import PortfolioLink
from .forms import PortfolioLinkForm
from .utils import fetch_og_image, fetch_og_title


# Return absolute URL for any given path or URL - KR 15/08/2025
def _abs(request, url_or_path: str) -> str:
    return request.build_absolute_uri(url_or_path)


# Return absolute URL to default OG image (hashed in prod if available) - KR 15/08/2025
def _default_og_abs(request) -> str:
    try:
        url = staticfiles_storage.url("images/og/portfolio-default.jpg")
    except Exception:
        url = static("images/og/portfolio-default.jpg")
    return _abs(request, url)


# Compute absolute display image URL for a given PortfolioLink - KR 15/08/2025
def _display_image_abs(request, link: PortfolioLink) -> str:
    img = None
    try:
        if getattr(link, "image_file", None) and getattr(link.image_file, "url", None):
            img = link.image_file.url
    except Exception:
        img = None

    if not img:
        img = getattr(link, "image_url", None)

    if img:
        if img.startswith(("http://", "https://")):
            return img
        return _abs(request, img)

    return _default_og_abs(request)


@login_required
def portfolio_gallery(request):
    """
    Owner's private gallery.
    - Adds absolute display images.
    - Adds absolute per-link URL for sharing.
    - Exposes a public_abs_url to share the whole portfolio page.
    """
    links = PortfolioLink.objects.filter(owner=request.user).order_by("-created_at")

    for l in links:
        # Prefer model's own display_image method if callable, otherwise compute - KR 15/08/2025
        if hasattr(l, "display_image") and callable(l.display_image):
            try:
                di = l.display_image(request)
            except TypeError:
                di = l.display_image()
            l.display_image = di
        else:
            l.display_image = _display_image_abs(request, l)

        # Absolute URL to detail/public-facing page for sharing - KR 15/08/2025
        if hasattr(l, "get_absolute_url") and callable(l.get_absolute_url):
            l.absolute_url = _abs(request, l.get_absolute_url())
        else:
            l.absolute_url = getattr(l, "url", "")

    og_image = links[0].display_image if links else _default_og_abs(request)

    public_path = reverse("portfolio:portfolio_public", args=[request.user.username])
    public_abs_url = _abs(request, public_path)

    return render(
        request,
        "portfolio/gallery.html",
        {
            "links": links,
            "og_image": og_image,
            "public_abs_url": public_abs_url,  # used for Share my portfolio button - KR 15/08/2025
        },
    )


@login_required
def portfolio_create(request):
    # Create new portfolio link - KR 15/08/2025
    if request.method == "POST":
        form = PortfolioLinkForm(request.POST, request.FILES)
        if form.is_valid():
            link = form.save(commit=False)
            link.owner = request.user
            link.save()
            if hasattr(link, "ensure_preview"):
                link.ensure_preview()  # populate OG metadata - KR 15/08/2025
            messages.success(request, "Link added to your portfolio.")
            return redirect("portfolio:portfolio_gallery")
    else:
        form = PortfolioLinkForm()
    return render(request, "portfolio/create.html", {"form": form})


def portfolio_public(request, username):
    """
    Public portfolio page.
    - Only shows published links.
    - Adds absolute display images & per-link share URLs.
    - Provides og_image & share_page_url for social previews / share buttons.
    """
    owner = get_object_or_404(User, username=username)
    links = PortfolioLink.objects.filter(owner=owner, is_published=True).order_by("-created_at")

    for l in links:
        l.display_image = _display_image_abs(request, l)
        if hasattr(l, "get_absolute_url") and callable(l.get_absolute_url):
            l.absolute_url = _abs(request, l.get_absolute_url())
        else:
            l.absolute_url = getattr(l, "url", "")

    og_image = links[0].display_image if links else _default_og_abs(request)
    share_page_url = _abs(request, request.path)

    return render(
        request,
        "portfolio/public.html",
        {
            "owner": owner,
            "links": links,
            "og_image": og_image,
            "share_page_url": share_page_url,  # page-level share link - KR 15/08/2025
        },
    )


@login_required
def portfolio_delete(request, slug):
    # Delete an existing portfolio link - KR 15/08/2025
    link = get_object_or_404(PortfolioLink, slug=slug, owner=request.user)

    if request.method == "POST":
        link.delete()
        messages.success(request, "Portfolio link deleted successfully.")
        return redirect("portfolio:portfolio_gallery")

    return redirect("portfolio:portfolio_gallery")


@login_required
def preview_api(request):
    """
    AJAX endpoint used by form JS to fetch OG title & image
    """
    url = (request.GET.get("url") or "").strip()
    if not url:
        return HttpResponseBadRequest("missing url")

    title = fetch_og_title(url) or ""
    image = fetch_og_image(url) or ""
    return JsonResponse({"title": title, "image_url": image})