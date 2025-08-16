from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from projects.models import Project

_TEST_OVERRIDES = dict(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)

@override_settings(**_TEST_OVERRIDES)
class ProjectViewTests(TestCase):
    def setUp(self):
        # Users
        self.owner = User.objects.create_user(
            username="owner", email="owner@example.com", password="pass12345"
        )
        self.collab = User.objects.create_user(
            username="collab", email="collab@example.com", password="pass12345"
        )
        self.stranger = User.objects.create_user(
            username="stranger", email="stranger@example.com", password="pass12345"
        )

        # Project
        self.project = Project.objects.create(
            title="Test Project",
            description="Desc",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="ongoing",
            category="other",
            owner=self.owner,
        )
        self.project.collaborators.add(self.collab)

    # Create

    def test_create_requires_login(self):
        url = reverse("create_project")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/users/login/", resp.headers.get("Location", ""))

    def test_create_owner_ok(self):
        self.client.login(username="owner", password="pass12345")
        url = reverse("create_project")
        payload = {
            "title": "NewProj",
            "description": "d",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "status": "ongoing",
            "category": "other",
            "invite_emails": "",
        }
        resp = self.client.post(url, payload, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Project.objects.filter(title="NewProj", owner=self.owner).exists())

    # Detail access control

    def test_detail_owner_access(self):
        self.client.login(username="owner", password="pass12345")
        url = reverse("project_detail", kwargs={"pk": self.project.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Test Project")

    def test_detail_collaborator_access(self):
        self.client.login(username="collab", password="pass12345")
        url = reverse("project_detail", kwargs={"pk": self.project.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Test Project")

    def test_detail_stranger_redirects_to_dashboard(self):
        self.client.login(username="stranger", password="pass12345")
        url = reverse("project_detail", kwargs={"pk": self.project.pk})
        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        # Should not show project title after redirect
        self.assertNotIn("Test Project", resp.content.decode())

    # Edit 

    def test_edit_owner_ok(self):
        self.client.login(username="owner", password="pass12345")
        url = reverse("edit_project", kwargs={"pk": self.project.pk})
        payload = {
            "title": "Edited Title",
            "description": "Desc",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "status": "ongoing",
            "category": "other",
            "invite_emails": "",
        }
        resp = self.client.post(url, payload, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Edited Title")

    def test_edit_collaborator_forbidden(self):
        self.client.login(username="collab", password="pass12345")
        url = reverse("edit_project", kwargs={"pk": self.project.pk})
        payload = {
            "title": "Should Not Change",
            "description": "x",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "status": "ongoing",
            "category": "other",
        }
        resp = self.client.post(url, payload, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.project.refresh_from_db()
        self.assertNotEqual(self.project.title, "Should Not Change")

    # Delete

    def test_delete_collaborator_forbidden(self):
        self.client.login(username="collab", password="pass12345")
        url = reverse("delete_project", kwargs={"pk": self.project.pk})
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_delete_owner_ok(self):
        self.client.login(username="owner", password="pass12345")
        url = reverse("delete_project", kwargs={"pk": self.project.pk})
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    # Status update API

    def test_update_status_owner_ok(self):
        self.client.login(username="owner", password="pass12345")
        url = reverse("update_project_status", kwargs={"pk": self.project.pk})
        resp = self.client.post(
            url,
            data='{"status":"completed"}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "completed")

    def test_update_status_non_owner_forbidden(self):
        self.client.login(username="collab", password="pass12345")
        url = reverse("update_project_status", kwargs={"pk": self.project.pk})
        resp = self.client.post(
            url,
            data='{"status":"paused"}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)
        self.project.refresh_from_db()
        self.assertNotEqual(self.project.status, "paused")