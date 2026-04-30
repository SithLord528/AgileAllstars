"""
Sprint CRUD and Lifecycle Tests

Create, activate, and close sprints through the views.
PM is logged in and a project already exists.

NOTE: activate_sprint and close_sprint no longer check for
request.method == 'POST', so GET requests also change state now.
"""

from django.urls import reverse

from sprints.models import Sprint
from .base import MultiDBTestCase


class CreateSprintTests(MultiDBTestCase):

    def setUp(self):
        super().setUp()
        self.login_as_pm()
        self.project = self.create_project()

    def test_create_sprint_success(self):
        """Fill in the sprint form — should start in PLANNING status."""
        url = reverse('create_sprint', kwargs={'project_id': self.project.id})
        response = self.client.post(url, {
            'name': 'Sprint 1',
            'goal': 'Complete login feature',
            'start_date': '2024-03-01',
            'end_date': '2024-03-14',
        })
        self.assertRedirects(
            response,
            reverse('project_board', kwargs={'project_id': self.project.id}),
        )
        sprint = Sprint.objects.get(name='Sprint 1')
        self.assertEqual(sprint.status, 'PLANNING')
        self.assertEqual(sprint.project, self.project)

    def test_create_sprint_minimal_fields(self):
        """Only the name is required — goal can be blank."""
        url = reverse('create_sprint', kwargs={'project_id': self.project.id})
        self.client.post(url, {'name': 'Sprint Min', 'goal': ''})
        self.assertTrue(Sprint.objects.filter(name='Sprint Min').exists())

    def test_create_sprint_empty_name_rejected(self):
        url = reverse('create_sprint', kwargs={'project_id': self.project.id})
        self.client.post(url, {'name': '', 'goal': ''})
        self.assertEqual(Sprint.objects.count(), 0)

    def test_create_sprint_unique_names_work(self):
        """Two sprints with different names in the same project — both created."""
        url = reverse('create_sprint', kwargs={'project_id': self.project.id})
        self.client.post(url, {'name': 'Sprint A', 'goal': ''})
        self.client.post(url, {'name': 'Sprint B', 'goal': ''})
        self.assertEqual(Sprint.objects.filter(project=self.project).count(), 2)


class ActivateSprintTests(MultiDBTestCase):

    def setUp(self):
        super().setUp()
        self.login_as_pm()
        self.project = self.create_project()

    def test_activate_sprint(self):
        sprint = self.create_sprint(self.project, status='PLANNING')
        url = reverse('activate_sprint', kwargs={'sprint_id': sprint.id})
        self.client.post(url)
        sprint.refresh_from_db()
        self.assertEqual(sprint.status, 'ACTIVE')

    def test_activating_new_sprint_closes_previous(self):
        """Only one sprint can be active at a time — the old one gets closed."""
        s1 = self.create_sprint(self.project, name='S1', status='ACTIVE')
        s2 = self.create_sprint(self.project, name='S2', status='PLANNING')

        url = reverse('activate_sprint', kwargs={'sprint_id': s2.id})
        self.client.post(url)

        s1.refresh_from_db()
        s2.refresh_from_db()
        self.assertEqual(s1.status, 'CLOSED')
        self.assertEqual(s2.status, 'ACTIVE')

    def test_get_activate_also_changes_status(self):
        """The view doesn't check for POST, so GET also activates."""
        sprint = self.create_sprint(self.project, status='PLANNING')
        url = reverse('activate_sprint', kwargs={'sprint_id': sprint.id})
        self.client.get(url)
        sprint.refresh_from_db()
        self.assertEqual(sprint.status, 'ACTIVE')


class CloseSprintTests(MultiDBTestCase):

    def setUp(self):
        super().setUp()
        self.login_as_pm()
        self.project = self.create_project()

    def test_close_sprint(self):
        sprint = self.create_sprint(self.project, status='ACTIVE')
        url = reverse('close_sprint', kwargs={'sprint_id': sprint.id})
        self.client.post(url)
        sprint.refresh_from_db()
        self.assertEqual(sprint.status, 'CLOSED')

    def test_get_close_also_changes_status(self):
        """The view doesn't check for POST, so GET also closes."""
        sprint = self.create_sprint(self.project, status='ACTIVE')
        url = reverse('close_sprint', kwargs={'sprint_id': sprint.id})
        self.client.get(url)
        sprint.refresh_from_db()
        self.assertEqual(sprint.status, 'CLOSED')


class SprintPropertyTests(MultiDBTestCase):
    """Check the model properties like item_counts and completion %."""

    def test_item_counts(self):
        project = self.create_project()
        sprint = self.create_sprint(project, status='ACTIVE')
        self.create_item(project, title='A', status='SPRINT', sprint=sprint)
        self.create_item(project, title='B', status='SPRINT', sprint=sprint)
        self.create_item(project, title='C', status='DONE', sprint=sprint)

        counts = sprint.item_counts
        self.assertEqual(counts.get('SPRINT', 0), 2)
        self.assertEqual(counts.get('DONE', 0), 1)
        self.assertEqual(counts['total'], 3)

    def test_completion_percentage(self):
        """1 done out of 2 = 50%."""
        project = self.create_project()
        sprint = self.create_sprint(project, status='ACTIVE')
        self.create_item(project, title='Done Item', status='DONE', sprint=sprint)
        self.create_item(project, title='Open Item', status='SPRINT', sprint=sprint)
        self.assertEqual(sprint.completion_percentage, 50.0)

    def test_completion_percentage_empty_sprint(self):
        project = self.create_project()
        sprint = self.create_sprint(project, status='ACTIVE')
        self.assertEqual(sprint.completion_percentage, 0)

    def test_str_representation(self):
        project = self.create_project(name='My Project')
        sprint = self.create_sprint(project, name='Sprint 1')
        self.assertIn('My Project', str(sprint))
        self.assertIn('Sprint 1', str(sprint))
