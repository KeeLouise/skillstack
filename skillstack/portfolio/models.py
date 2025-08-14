from django.conf import settings
from django.core.validators import URLValidator
from django.db import models
from django.utils.text import slugify

class PortfolioLink(models.Model):
    owner       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portfolio_links")
    title       = models.CharField(max_length=120)
    url         = models.URLField()
    image_url   = models.URLField(blank=True)
    image_file  = models.ImageField(upload_to="portfolio_thumbs/", blank=True, null=True)
    slug        = models.SlugField(max_length=140, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("owner", "slug")]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title or self.url)
            s = base
            n = 1
            while PortfolioLink.objects.filter(owner=self.owner, slug=s).exclude(pk=self.pk).exists():
                n += 1
                s = f"{base}-{n}"
            self.slug = s
        super().save(*args, **kwargs)

    def display_image(self):
        if self.image_file:
            return self.image_file.url
        if self.image_url:
            return self.image_url
        return "data:image/svg+xml;utf8," \
               "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 630'>" \
               "<defs><linearGradient id='g' x1='0' x2='1'><stop stop-color='%234f7dbb'/>" \
               "<stop offset='1' stop-color='%237ad1c4'/></linearGradient></defs>" \
               "<rect width='1200' height='630' fill='url(%23g)'/>" \
               "</svg>"