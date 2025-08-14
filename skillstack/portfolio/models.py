from django.db import models
from django.contrib.auth import get_user_model
from django.templatetags.static import static
from django.utils.text import slugify

from .utils import fetch_og_image

User = get_user_model()

class PortfolioLink(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="portfolio_links")
    title = models.CharField(max_length=200, blank=True)
    url = models.URLField()
    slug = models.SlugField(max_length=140, blank=True)
    image_file = models.ImageField(upload_to="portfolio/thumbs/", blank=True, null=True)
    image_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "slug"], name="portfolio_owner_slug_unique"),
        ]
        indexes = [
            models.Index(fields=["owner", "-created_at"]),
        ]

    def __str__(self):
        return self.title or self.url

    def save(self, *args, **kwargs):
        # Auto-create a slug (unique per owner) if missing
        if not self.slug:
            base = slugify(self.title or self.url) or "link"
            candidate = base
            i = 1
            while PortfolioLink.objects.filter(owner=self.owner, slug=candidate).exclude(pk=self.pk).exists():
                i += 1
                candidate = f"{base}-{i}"
            self.slug = candidate
        super().save(*args, **kwargs)

    def display_image(self, request=None) -> str:
        """
        Returns a preview image URL.
        - Prefers uploaded file, then scraped image_url, then static fallback.
        - If `request` is provided and the URL is relative, it returns an absolute URL (good for OG).
        """
        url = ""
        if self.image_file and getattr(self.image_file, "url", None):
            url = self.image_file.url
        elif self.image_url:
            url = self.image_url
        else:
            url = static("images/og/portfolio-default.jpg")

        if request and not (url.startswith("http://") or url.startswith("https://")):
            return request.build_absolute_uri(url)
        return url

    def ensure_preview(self, force: bool = False) -> bool:
        """
        Populate image_url from target site if missing (or force). Returns True if updated.
        """
        if self.image_file:
            return False
        if self.image_url and not force:
            return False

        img = fetch_og_image(self.url)
        if img:
            self.image_url = img
            self.save(update_fields=["image_url"])
            return True
        return False