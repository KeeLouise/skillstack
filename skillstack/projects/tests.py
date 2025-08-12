from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from projects.models import Project, Invitation
from datetime import date

class ProjectModelFormViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', email='owner@example.com', password='pass12345')
        self.collab = User.objects.create_user(username='collab', email='collab@example.com', password='pass12345')
        self.stranger = User.objects.create_user(username='stranger', email='stranger@example.com', password='pass12345')

        self.project = Project.objects.create(
            title="Test Project",
            description="Desc",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status='ongoing',
            category='other',
            owner=self.owner,
        )
        self.project.collaborators.add(self.collab)

    def test_model_str(self):
        self.assertEqual(str(self.project), "Test Project")

    def test_create_project_requires_login(self):
        url = reverse('create_project')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/users/login/', resp.headers.get('Location', ''))

    def test_create_project_ok(self):
        self.client.login(username='owner', password='pass12345')
        url = reverse('create_project')
        payload = {
            'title': 'NewProj',
            'description': 'd',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
            'status': 'ongoing',
            'category': 'other',
            'invite_emails': '',
        }
        resp = self.client.post(url, payload, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Project.objects.filter(title='NewProj', owner=self.owner).exists())

    def test_project_detail_access_owner(self):
        self.client.login(username='owner', password='pass12345')
        url = reverse('project_detail', kwargs={'pk': self.project.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_project_detail_access_collaborator(self):
        self.client.login(username='collab', password='pass12345')
        url = reverse('project_detail', kwargs={'pk': self.project.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_project_detail_forbidden_for_stranger(self):
        self.client.login(username='stranger', password='pass12345')
        url = reverse('project_detail', kwargs={'pk': self.project.pk})
        resp = self.client.get(url, follow=True)
        # Should redirect to dashboard with error message, not 200 on detail
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('Test Project', resp.content.decode())

    def test_edit_project_owner_only(self):
        # owner can edit
        self.client.login(username='owner', password='pass12345')
        url = reverse('edit_project', kwargs={'pk': self.project.pk})
        resp = self.client.post(url, {
            'title': 'Edited Title',
            'description': 'Desc',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
            'status': 'ongoing',
            'category': 'other',
            'invite_emails': '',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, 'Edited Title')

        # collaborator cannot edit
        self.client.logout()
        self.client.login(username='collab', password='pass12345')
        resp2 = self.client.post(url, {
            'title': 'Nope',
            'description': 'x',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
            'status': 'ongoing',
            'category': 'other',
        }, follow=True)
        self.project.refresh_from_db()
        self.assertNotEqual(self.project.title, 'Nope')

    def test_delete_project_owner_only(self):
        url = reverse('delete_project', kwargs={'pk': self.project.pk})

        # collaborator cannot delete
        self.client.login(username='collab', password='pass12345')
        resp = self.client.post(url, follow=True)
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

        # owner can delete
        self.client.logout()
        self.client.login(username='owner', password='pass12345')
        resp2 = self.client.post(url, follow=True)
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())