"""
Model-Level CRUD Tests

Straight-up ORM tests for every model: create, read, update, delete.
Both the default and projects databases need to be available.
"""

from django.test import RequestFactory
from django.contrib.auth.models import User

from sprints.models import Project, Sprint, BacklogItem, StageComment
from taskStatus.models import Task
from .base import MultiDBTestCase


# ======================================================================
#  Project Model
# ======================================================================

class ProjectModelCRUDTests(MultiDBTestCase):

    def test_create(self):
        project = Project.objects.create(
            name='CRUD Project', description='Testing', owner_id=self.pm_user.id,
        )
        self.assertIsNotNone(project.pk)
        self.assertEqual(project.name, 'CRUD Project')

    def test_read(self):
        project = self.create_project(name='Readable')
        fetched = Project.objects.get(pk=project.pk)
        self.assertEqual(fetched.name, 'Readable')

    def test_update(self):
        project = self.create_project(name='Old Name')
        project.name = 'New Name'
        project.save()
        project.refresh_from_db()
        self.assertEqual(project.name, 'New Name')

    def test_delete(self):
        project = self.create_project()
        pk = project.pk
        project.delete()
        self.assertFalse(Project.objects.filter(pk=pk).exists())

    def test_owner_property_resolves(self):
        """owner property should give us the actual User object."""
        project = self.create_project(owner=self.pm_user)
        self.assertEqual(project.owner, self.pm_user)

    def test_owner_property_missing_user(self):
        """If the owner was deleted, should return None instead of crashing."""
        project = self.create_project()
        project.owner_id = 99999
        project.save()
        self.assertIsNone(project.owner)

    def test_collaborator_ids_default_empty(self):
        project = self.create_project()
        self.assertEqual(project.collaborator_ids, [])

    def test_collaborators_property(self):
        """Add some collaborator IDs and check the property returns
        the right User objects."""
        project = self.create_project()
        project.collaborator_ids = [self.dev_user.id, self.dev_user2.id]
        project.save()
        collabs = set(project.collaborators.values_list('id', flat=True))
        self.assertEqual(collabs, {self.dev_user.id, self.dev_user2.id})

    def test_str(self):
        project = self.create_project(name='StrTest')
        self.assertEqual(str(project), 'StrTest')


# ======================================================================
#  Sprint Model
# ======================================================================

class SprintModelCRUDTests(MultiDBTestCase):

    def test_create(self):
        project = self.create_project()
        sprint = Sprint.objects.create(
            project=project, name='Sprint CRUD', goal='Test goal',
        )
        self.assertIsNotNone(sprint.pk)
        self.assertEqual(sprint.status, 'PLANNING')

    def test_read(self):
        project = self.create_project()
        sprint = self.create_sprint(project, name='Readable Sprint')
        fetched = Sprint.objects.get(pk=sprint.pk)
        self.assertEqual(fetched.name, 'Readable Sprint')

    def test_update(self):
        project = self.create_project()
        sprint = self.create_sprint(project, name='Old Sprint')
        sprint.name = 'Renamed Sprint'
        sprint.save()
        sprint.refresh_from_db()
        self.assertEqual(sprint.name, 'Renamed Sprint')

    def test_delete(self):
        project = self.create_project()
        sprint = self.create_sprint(project)
        pk = sprint.pk
        sprint.delete()
        self.assertFalse(Sprint.objects.filter(pk=pk).exists())

    def test_cascade_delete_with_project(self):
        """Delete the project — all its sprints should go with it."""
        project = self.create_project()
        self.create_sprint(project)
        project.delete()
        self.assertEqual(Sprint.objects.count(), 0)

    def test_default_ordering(self):
        project = self.create_project()
        s1 = self.create_sprint(project, name='First')
        s2 = self.create_sprint(project, name='Second')
        sprints = list(Sprint.objects.filter(project=project))
        self.assertEqual(sprints[0].name, 'Second')


# ======================================================================
#  BacklogItem Model
# ======================================================================

class BacklogItemModelCRUDTests(MultiDBTestCase):

    def test_create(self):
        project = self.create_project()
        item = BacklogItem.objects.create(
            project=project, title='CRUD Item',
            created_by_id=self.pm_user.id,
        )
        self.assertIsNotNone(item.pk)
        self.assertEqual(item.status, 'BACKLOG')
        self.assertEqual(item.priority, 'MED')

    def test_read(self):
        project = self.create_project()
        item = self.create_item(project, title='Readable Item')
        fetched = BacklogItem.objects.get(pk=item.pk)
        self.assertEqual(fetched.title, 'Readable Item')

    def test_update(self):
        project = self.create_project()
        item = self.create_item(project, title='Old Title')
        item.title = 'New Title'
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.title, 'New Title')

    def test_delete(self):
        project = self.create_project()
        item = self.create_item(project)
        pk = item.pk
        item.delete()
        self.assertFalse(BacklogItem.objects.filter(pk=pk).exists())

    def test_cascade_delete_with_project(self):
        """Delete the project — all its items should go with it."""
        project = self.create_project()
        self.create_item(project)
        project.delete()
        self.assertEqual(BacklogItem.objects.count(), 0)

    def test_sprint_set_null_on_delete(self):
        """If the sprint gets deleted, the item should still exist
        but with sprint set to None."""
        project = self.create_project()
        sprint = self.create_sprint(project)
        item = self.create_item(project, sprint=sprint)
        sprint.delete()
        item.refresh_from_db()
        self.assertIsNone(item.sprint)

    def test_assigned_to_property(self):
        project = self.create_project()
        item = self.create_item(project, assigned_to_id=self.dev_user.id)
        self.assertEqual(item.assigned_to, self.dev_user)

    def test_assigned_to_none(self):
        project = self.create_project()
        item = self.create_item(project)
        self.assertIsNone(item.assigned_to)

    def test_assigned_to_missing_user(self):
        """If the assigned user was deleted, returns None."""
        project = self.create_project()
        item = self.create_item(project, assigned_to_id=99999)
        self.assertIsNone(item.assigned_to)

    def test_created_by_property(self):
        project = self.create_project()
        item = self.create_item(project, creator=self.pm_user)
        self.assertEqual(item.created_by, self.pm_user)

    def test_created_by_missing_user(self):
        project = self.create_project()
        item = self.create_item(project)
        item.created_by_id = 99999
        item.save()
        self.assertIsNone(item.created_by)

    def test_can_transition_to(self):
        project = self.create_project()
        item = self.create_item(project, status='BACKLOG')
        self.assertTrue(item.can_transition_to('SPRINT'))
        self.assertFalse(item.can_transition_to('TEST'))
        self.assertFalse(item.can_transition_to('DONE'))

    def test_str(self):
        project = self.create_project()
        item = self.create_item(project, title='My Task', status='BACKLOG')
        self.assertIn('My Task', str(item))

    def test_ordering(self):
        """Items are sorted by -priority then -updated_at. The priority
        field stores strings (LOW, MED, HIGH, CRIT) so Django sorts them
        alphabetically, not semantically. MED > LOW > HIGH > CRIT in
        alphabetical order. This is a known tech debt item."""
        project = self.create_project()
        self.create_item(project, title='Low', priority='LOW')
        self.create_item(project, title='Med', priority='MED')
        items = list(BacklogItem.objects.filter(project=project))
        self.assertEqual(items[0].title, 'Med')


# ======================================================================
#  StageComment Model
# ======================================================================

class StageCommentModelCRUDTests(MultiDBTestCase):

    def test_create(self):
        project = self.create_project()
        item = self.create_item(project)
        comment = StageComment.objects.create(
            item=item, author_id=self.pm_user.id,
            from_stage='BACKLOG', to_stage='SPRINT',
            body='Created via CRUD test',
        )
        self.assertIsNotNone(comment.pk)

    def test_read(self):
        project = self.create_project()
        item = self.create_item(project)
        comment = self.create_comment(item, body='Read me')
        fetched = StageComment.objects.get(pk=comment.pk)
        self.assertEqual(fetched.body, 'Read me')

    def test_update(self):
        project = self.create_project()
        item = self.create_item(project)
        comment = self.create_comment(item, body='Original')
        comment.body = 'Edited'
        comment.save()
        comment.refresh_from_db()
        self.assertEqual(comment.body, 'Edited')

    def test_delete(self):
        project = self.create_project()
        item = self.create_item(project)
        comment = self.create_comment(item)
        pk = comment.pk
        comment.delete()
        self.assertFalse(StageComment.objects.filter(pk=pk).exists())


# ======================================================================
#  Task Model (legacy taskStatus.Task — not actively used but still in the DB)
# ======================================================================

class TaskModelCRUDTests(MultiDBTestCase):
    """CRUD for the old Task model that lives in the default database."""

    def test_create(self):
        task = Task.objects.create(
            title='Legacy Task', description='Old model',
            status='TODO', user=self.pm_user,
        )
        self.assertIsNotNone(task.pk)

    def test_read(self):
        task = Task.objects.create(
            title='Readable', user=self.pm_user,
        )
        fetched = Task.objects.get(pk=task.pk)
        self.assertEqual(fetched.title, 'Readable')

    def test_update(self):
        task = Task.objects.create(title='Old', user=self.pm_user)
        task.title = 'New'
        task.save()
        task.refresh_from_db()
        self.assertEqual(task.title, 'New')

    def test_delete(self):
        task = Task.objects.create(title='Deletable', user=self.pm_user)
        pk = task.pk
        task.delete()
        self.assertFalse(Task.objects.filter(pk=pk).exists())

    def test_cascade_delete_with_user(self):
        """Delete the user — their tasks should go with them."""
        temp = User.objects.create_user(username='temp', password='x')
        Task.objects.create(title='Temp Task', user=temp)
        temp.delete()
        self.assertEqual(Task.objects.filter(user_id=temp.id).count(), 0)

    def test_default_status(self):
        task = Task.objects.create(title='Default', user=self.pm_user)
        self.assertEqual(task.status, 'TODO')

    def test_str(self):
        task = Task.objects.create(title='Str Test', user=self.pm_user)
        self.assertIn('Str Test', str(task))
