"""
Test Case 2 - Create New Project  (F2-001 through F2-004)

PM needs to be logged in. Project list lives at /.
"""

from django.urls import reverse

from sprints.models import Project
from .base import MultiDBTestCase


class CreateProjectTests(MultiDBTestCase):
    """Create projects through the UI and make sure the form catches bad input."""

    # -- F2-001: Create a project the normal way --
    def test_F2_001_create_project_success(self):
        """Fill in the name, hit create — should show up on the dashboard."""
        self.login_as_pm()
        response = self.client.post(
            reverse('project_list'),
            {'name': 'E-Commerce Platform', 'description': 'Online shop'},
        )
        project = Project.objects.get(name='E-Commerce Platform')
        self.assertRedirects(
            response,
            reverse('project_board', kwargs={'project_id': project.id}),
        )
        self.assertEqual(project.owner_id, self.pm_user.id)

    # -- F2-002: Create a bunch of projects back to back --
    def test_F2_002_create_multiple_projects(self):
        """All three should show up on the dashboard independently."""
        self.login_as_pm()
        for name in ('Project Alpha', 'Project Beta', 'Project Gamma'):
            self.client.post(reverse('project_list'), {'name': name, 'description': ''})

        self.assertEqual(Project.objects.count(), 3)
        response = self.client.get(reverse('project_list'))
        content = response.content.decode()
        for name in ('Project Alpha', 'Project Beta', 'Project Gamma'):
            self.assertIn(name, content)

    # -- F2-003: Try to create a project with no name --
    def test_F2_003_empty_name_rejected(self):
        """Blank name — form should reject it, nothing saved."""
        self.login_as_pm()
        response = self.client.post(
            reverse('project_list'), {'name': '', 'description': ''}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Project.objects.count(), 0)

    # -- F2-004: Try to create a project with a name that already exists --
    def test_F2_004_duplicate_name_rejected(self):
        """Should get rejected because we added unique=True on Project.name."""
        self.login_as_pm()
        self.client.post(
            reverse('project_list'),
            {'name': 'E-Commerce Platform', 'description': ''},
        )
        response = self.client.post(
            reverse('project_list'),
            {'name': 'E-Commerce Platform', 'description': ''},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Project.objects.filter(name='E-Commerce Platform').count(), 1,
        )


class ProjectCRUDTests(MultiDBTestCase):
    """General CRUD stuff for projects — read, delete, completion %."""

    def test_create_project_sets_owner(self):
        """The person who creates the project should be the owner."""
        self.login_as_pm()
        self.client.post(reverse('project_list'), {'name': 'My Proj', 'description': ''})
        project = Project.objects.get(name='My Proj')
        self.assertEqual(project.owner_id, self.pm_user.id)

    def test_read_project_board(self):
        """Should be able to GET the board and see the project name."""
        self.login_as_pm()
        project = self.create_project(name='Board Test')
        response = self.client.get(reverse('project_board', kwargs={'project_id': project.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Board Test')

    def test_read_project_list_shows_only_own_projects(self):
        """You should only see projects you own or collaborate on."""
        self.login_as_pm()
        self.create_project(name='PM Project', owner=self.pm_user)
        self.create_project(name='Dev Project', owner=self.dev_user)
        response = self.client.get(reverse('project_list'))
        self.assertContains(response, 'PM Project')
        self.assertNotContains(response, 'Dev Project')

    def test_read_project_list_includes_collab_projects(self):
        """If you're added as a collaborator, that project should show up too."""
        self.login_as_dev()
        project = self.create_project(name='Collab Project', owner=self.pm_user)
        project.collaborator_ids = [self.dev_user.id]
        project.save()
        response = self.client.get(reverse('project_list'))
        self.assertContains(response, 'Collab Project')

    def test_delete_project_by_owner(self):
        """Owner POSTs to delete — project should be gone."""
        self.login_as_pm()
        project = self.create_project()
        response = self.client.post(
            reverse('delete_project', kwargs={'project_id': project.id})
        )
        self.assertRedirects(response, reverse('project_list'))
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_delete_project_nonexistent_404(self):
        self.login_as_pm()
        response = self.client.post(
            reverse('delete_project', kwargs={'project_id': 99999})
        )
        self.assertEqual(response.status_code, 404)

    def test_project_completion_percentage_empty(self):
        project = self.create_project()
        self.assertEqual(project.completion_percentage, 0)

    def test_project_completion_percentage_with_items(self):
        """1 done out of 2 total = 50%."""
        project = self.create_project()
        self.create_item(project, title='Done Task', status='DONE')
        self.create_item(project, title='Open Task', status='BACKLOG')
        self.assertEqual(project.completion_percentage, 50.0)
