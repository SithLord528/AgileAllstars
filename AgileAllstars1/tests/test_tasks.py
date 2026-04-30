"""
Test Case 3 - Create, Edit, and Delete Tasks  (F3-001 through F3-005)

PM is logged in and has a project ready to go.

NOTE: The BacklogItemForm in sprints/forms.py no longer includes
start_date/end_date fields, so date validation is not enforced
through the form. The model still has the fields — they just aren't
exposed in the create form anymore.
"""

from django.urls import reverse

from sprints.models import BacklogItem
from .base import MultiDBTestCase


class CreateTaskTests(MultiDBTestCase):
    """Create tasks, edit them via item_detail, delete them,
    and make sure the form catches bad input."""

    def setUp(self):
        super().setUp()
        self.login_as_pm()
        self.project = self.create_project()

    # -- F3-001: Create a task the normal way --
    def test_F3_001_create_task_success(self):
        """Should land in the Product Backlog with all the details we entered."""
        url = reverse('create_item', kwargs={'project_id': self.project.id})
        response = self.client.post(url, {
            'title': 'Design Login Page',
            'description': 'Create wireframes for login UI',
            'priority': 'HIGH',
        })
        self.assertRedirects(
            response,
            reverse('project_board', kwargs={'project_id': self.project.id}),
        )
        item = BacklogItem.objects.get(title='Design Login Page')
        self.assertEqual(item.status, 'BACKLOG')
        self.assertEqual(item.priority, 'HIGH')
        self.assertEqual(item.created_by_id, self.pm_user.id)
        self.assertEqual(item.project_id, self.project.id)

    # -- F3-002: Edit the title, description, assignee, and priority --
    def test_F3_002_edit_task_title_and_description(self):
        """POST to item_detail with new values — everything should update."""
        item = self.create_item(self.project, title='Design Login Page')
        # Add dev as a collaborator so we can assign to them
        self.project.collaborator_ids = [self.dev_user.id]
        self.project.save()

        url = reverse('item_detail', kwargs={'item_id': item.id})
        response = self.client.post(url, {
            'action': 'update_details',
            'title': 'Design Login & Registration Page',
            'description': 'Updated description for login + reg',
            'assignee': str(self.dev_user.id),
            'priority': 'CRIT',
        })
        self.assertRedirects(response, url)

        item.refresh_from_db()
        self.assertEqual(item.title, 'Design Login & Registration Page')
        self.assertEqual(item.description, 'Updated description for login + reg')
        self.assertEqual(item.assigned_to_id, self.dev_user.id)
        self.assertEqual(item.priority, 'CRIT')

    # -- F3-003: Delete a task --
    def test_F3_003_delete_task(self):
        """POST to delete — task should be gone from the database."""
        item = self.create_item(self.project)
        url = reverse('delete_item', kwargs={'item_id': item.id})
        response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse('project_board', kwargs={'project_id': self.project.id}),
        )
        self.assertFalse(BacklogItem.objects.filter(id=item.id).exists())

    # -- F3-004: Try creating a task with no title --
    def test_F3_004_empty_title_rejected(self):
        """Blank title — form should reject it, nothing saved."""
        url = reverse('create_item', kwargs={'project_id': self.project.id})
        self.client.post(url, {'title': '', 'description': '', 'priority': 'MED'})
        self.assertEqual(BacklogItem.objects.count(), 0)

    # -- F3-005: Date fields are no longer in BacklogItemForm --
    # The form in sprints/forms.py only has title, description, priority.
    # Dates passed in POST data are silently ignored by the form.
    def test_F3_005_dates_not_in_form(self):
        """Dates sent via POST are ignored since the form doesn't include them.
        The item still gets created with the other valid fields."""
        url = reverse('create_item', kwargs={'project_id': self.project.id})
        self.client.post(url, {
            'title': 'Date Test',
            'description': '',
            'priority': 'MED',
            'start_date': '2024-03-10',
            'end_date': '2024-03-05',
        })
        item = BacklogItem.objects.get(title='Date Test')
        # Dates are not saved because the form doesn't process them
        self.assertIsNone(item.start_date)
        self.assertIsNone(item.end_date)

    def test_F3_005b_dates_can_be_set_via_orm(self):
        """Dates still exist on the model — they can be set directly."""
        item = self.create_item(self.project, title='ORM Dated Task')
        item.start_date = '2024-03-01'
        item.end_date = '2024-03-10'
        item.save()
        item.refresh_from_db()
        self.assertEqual(str(item.start_date), '2024-03-01')
        self.assertEqual(str(item.end_date), '2024-03-10')


class TaskCRUDTests(MultiDBTestCase):
    """Extra CRUD coverage beyond what the spreadsheet asks for."""

    def setUp(self):
        super().setUp()
        self.login_as_pm()
        self.project = self.create_project()

    def test_create_multiple_tasks(self):
        url = reverse('create_item', kwargs={'project_id': self.project.id})
        for title in ('Task A', 'Task B', 'Task C'):
            self.client.post(url, {'title': title, 'description': '', 'priority': 'MED'})
        self.assertEqual(BacklogItem.objects.filter(project=self.project).count(), 3)

    def test_read_item_detail(self):
        item = self.create_item(self.project, title='Read Me')
        url = reverse('item_detail', kwargs={'item_id': item.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Read Me')

    def test_delete_nonexistent_item_404(self):
        response = self.client.post(
            reverse('delete_item', kwargs={'item_id': 99999})
        )
        self.assertEqual(response.status_code, 404)

    def test_get_delete_item_does_not_delete(self):
        """GET should NOT delete — only POST does."""
        item = self.create_item(self.project)
        self.client.get(reverse('delete_item', kwargs={'item_id': item.id}))
        self.assertTrue(BacklogItem.objects.filter(id=item.id).exists())

    def test_item_detail_clear_assignee(self):
        """Send an empty assignee field — should unassign the task."""
        item = self.create_item(self.project, assigned_to_id=self.dev_user.id)
        url = reverse('item_detail', kwargs={'item_id': item.id})
        self.client.post(url, {
            'action': 'update_details',
            'title': item.title,
            'description': '',
            'assignee': '',
            'priority': 'MED',
        })
        item.refresh_from_db()
        self.assertIsNone(item.assigned_to_id)
