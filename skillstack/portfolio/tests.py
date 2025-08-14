# Tests for Portfolio server-side - KR 14/08/2025
import os
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, RequestFactory, override_settings
from django.urls import reverse

from portfolio.models import PortfolioLink
from portfolio import views as portfolio_views

User = get_user_model()

# Test storage overrides 
# Use plain FileSystemStorage + StaticFilesStorage during tests 
_TMP_MEDIA = tempfile.mkdtemp(prefix="test_media_")
_TMP_STATIC = tempfile.mkdtemp(prefix="test_static_")

_TEST_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


@override_settings(
    STORAGES=_TEST_STORAGES,
    DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage",
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
    MEDIA_ROOT=_TMP_MEDIA,
    STATIC_ROOT=_TMP_STATIC,
    STATICFILES_DIRS=[],
)
class UsesLocalStoragesTestCase(TestCase):
    """Base class to ensure all inheriting test cases use local storages."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_TMP_MEDIA, ignore_errors=True)
        shutil.rmtree(_TMP_STATIC, ignore_errors=True)


#  Helper creation 

def make_user(username="alice", password="pass12345"):
    user = User.objects.create_user(username=username, password=password)
    return user, password


#  Server-side view & model tests

class PortfolioServerTests(UsesLocalStoragesTestCase):
    """
    Covers:
      - gallery/create/public views (auth & rendering)
      - create POST flow
      - owner-only delete
      - image selection helper (_display_image_abs)
      - basic URL reversing
    """

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.alice, self.alice_pw = make_user("alice")
        self.bob, self.bob_pw = make_user("bob")

    # GALLERY

    def test_gallery_requires_login_redirects(self):
        """Anonymous users should be redirected to login when opening gallery."""
        resp = self.client.get(reverse("portfolio:portfolio_gallery"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/users/login", resp.url)

    def test_gallery_renders_for_owner(self):
        """Logged-in owner should see their gallery listing."""
        self.client.login(username="alice", password=self.alice_pw)
        # Create two links for Alice, one for Bob (shouldn't appear)
        PortfolioLink.objects.create(owner=self.alice, title="A1", url="https://a1.example", slug="a1")
        PortfolioLink.objects.create(owner=self.alice, title="A2", url="https://a2.example", slug="a2")
        PortfolioLink.objects.create(owner=self.bob, title="B1", url="https://b1.example", slug="b1")

        resp = self.client.get(reverse("portfolio:portfolio_gallery"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "A1")
        self.assertContains(resp, "A2")
        self.assertNotContains(resp, "B1")

    # CREATE 

    def test_create_requires_login_and_renders(self):
        """GET /portfolio/new/ must require login; once logged, it renders."""
        # anonymous -> redirect
        resp = self.client.get(reverse("portfolio:portfolio_create"))
        self.assertEqual(resp.status_code, 302)

        # logged-in -> render
        self.client.login(username="alice", password=self.alice_pw)
        resp = self.client.get(reverse("portfolio:portfolio_create"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Add Link")

    def test_create_post_creates_link_and_redirects(self):
        """Valid POST should create a link for the logged-in user and redirect."""
        self.client.login(username="alice", password=self.alice_pw)
        data = {
            "title": "My Site",
            "url": "https://example.com/",
            # optional file/url fields omitted; model should handle gracefully
        }
        resp = self.client.post(reverse("portfolio:portfolio_create"), data, follow=True)
        self.assertEqual(resp.status_code, 200)  # landed on redirect target

        link = PortfolioLink.objects.get(owner=self.alice, url="https://example.com/")
        self.assertEqual(link.title, "My Site")
        # verify slug was set
        self.assertTrue(link.slug)

    # PUBLIC

    def test_public_is_anonymous_and_renders(self):
        """Public page should be accessible without login."""
        # Make some links for Alice
        PortfolioLink.objects.create(owner=self.alice, title="Pub1", url="https://p1.example", slug="pub-1", is_published=True)
        PortfolioLink.objects.create(owner=self.alice, title="Priv1", url="https://priv1.example", slug="priv-1", is_published=False)

        resp = self.client.get(reverse("portfolio:portfolio_public", args=[self.alice.username]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Pub1")
        self.assertNotContains(resp, "Priv1")

    def test_public_filters_is_published(self):
        """Only is_published=True links should appear on the public page."""
        PortfolioLink.objects.create(owner=self.alice, title="Shown", url="https://ok.example", slug="ok", is_published=True)
        PortfolioLink.objects.create(owner=self.alice, title="Hidden", url="https://nope.example", slug="nope", is_published=False)

        resp = self.client.get(reverse("portfolio:portfolio_public", args=[self.alice.username]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Shown")
        self.assertNotContains(resp, "Hidden")

    # DELETE

    def test_delete_only_owner(self):
        """Delete endpoint must only delete if the slug belongs to the logged-in owner."""
        link = PortfolioLink.objects.create(owner=self.alice, title="KillMe", url="https://del.example", slug="kill-me")

        # Bob cannot delete Alice's link -> 404 (object not found for this owner)
        self.client.login(username="bob", password=self.bob_pw)
        resp = self.client.post(reverse("portfolio:portfolio_delete", args=[link.slug]))
        self.assertEqual(resp.status_code, 404)

        # Alice can delete
        self.client.login(username="alice", password=self.alice_pw)
        resp = self.client.post(reverse("portfolio:portfolio_delete", args=[link.slug]), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(PortfolioLink.objects.filter(pk=link.pk).exists())

    # IMAGE CHOOSING HELPER 

    def test_display_image_abs_prefers_file_then_url_then_default(self):
        """
        _display_image_abs should:
          1) prefer uploaded file (absolute URL)
          2) fall back to image_url if absolute
          3) finally use default static image as absolute URL
        """
        # Build fake request for absolute URL building
        request = self.factory.get("/")
        request.user = self.alice

        # 1) With uploaded file
        up = SimpleUploadedFile("thumb.jpg", b"fake-bytes", content_type="image/jpeg")
        with_file = PortfolioLink.objects.create(
            owner=self.alice, title="WithFile", url="https://wf.example", slug="with-file", image_file=up
        )
        abs_url_1 = portfolio_views._display_image_abs(request, with_file)
        self.assertTrue(abs_url_1.startswith("http://testserver/")) 
        self.assertIn("/media/portfolio/thumbs/", abs_url_1)

        # 2) With image_url absolute
        with_url = PortfolioLink.objects.create(
            owner=self.alice, title="WithUrl", url="https://wu.example", slug="with-url", image_url="https://img.example/og.png"
        )
        abs_url_2 = portfolio_views._display_image_abs(request, with_url)
        self.assertEqual(abs_url_2, "https://img.example/og.png")

        # 3) Neither -> default static OG image
        neither = PortfolioLink.objects.create(
            owner=self.alice, title="Neither", url="https://n.example", slug="neither"
        )
        abs_url_3 = portfolio_views._display_image_abs(request, neither)
        self.assertTrue(abs_url_3.startswith("http://testserver/"))
        self.assertIn("/static/images/og/portfolio-default.jpg", abs_url_3)

    #  URL reversing

    def test_urls_reverse(self):
        """Basic reversing sanity checks for namespaced URLs."""
        self.assertTrue(reverse("portfolio:portfolio_gallery").endswith("/portfolio/"))
        self.assertTrue(reverse("portfolio:portfolio_create").endswith("/portfolio/new/"))
        self.assertTrue(reverse("portfolio:preview_api").endswith("/portfolio/preview/"))
        self.assertTrue(
            reverse("portfolio:portfolio_public", args=[self.alice.username]).endswith(f"/portfolio/p/{self.alice.username}/")
        )
        # delete expects a slug arg
        self.assertTrue(reverse("portfolio:portfolio_delete", args=["abc"]).endswith("/portfolio/delete/abc/"))