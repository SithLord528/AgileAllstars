"""
Shared test helpers for our test suite.

Since we use two databases (default for auth, projects for sprints data),
every test that touches Project/Sprint/BacklogItem/StageComment needs
databases = '__all__' so Django lets us write to both. These base classes
handle that so we don't have to remember it in every single file.
"""

from django.test import TestCase, TransactionTestCase, RequestFactory, Client
from django.contrib.auth.models import User
from sprints.models import Project, Sprint, BacklogItem, StageComment


class MultiDBTestCase(TestCase):
    """Base TestCase that works with both our databases and gives us
    some handy shortcuts for creating test data."""

    databases = '__all__'

    @classmethod
    def setUpTestData(cls):
        # Create a few users we can reuse across all tests
        cls.pm_user = User.objects.create_user(
            username='pm_user', email='pm@company.com', password='Test@1234!'
        )
        cls.dev_user = User.objects.create_user(
            username='dev_user', email='dev@company.com', password='DevPass@123'
        )
        cls.dev_user2 = User.objects.create_user(
            username='dev_user2', email='dev2@company.com', password='DevPass@456'
        )

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

    # -- Quick login helpers so we don't repeat credentials everywhere --

    def login_as_pm(self):
        self.client.login(username='pm_user', password='Test@1234!')

    def login_as_dev(self):
        self.client.login(username='dev_user', password='DevPass@123')

    def login_as_dev2(self):
        self.client.login(username='dev_user2', password='DevPass@456')

    # -- Shortcuts to spin up test data fast --

    def create_project(self, owner=None, name='Test Project', **kwargs):
        owner = owner or self.pm_user
        return Project.objects.create(name=name, owner_id=owner.id, **kwargs)

    def create_sprint(self, project, name='Sprint 1', status='PLANNING', **kwargs):
        return Sprint.objects.create(
            project=project, name=name, status=status, **kwargs
        )

    def create_item(self, project, title='Test Task', creator=None, **kwargs):
        creator = creator or self.pm_user
        defaults = {
            'status': 'BACKLOG',
            'priority': 'MED',
            'created_by_id': creator.id,
        }
        defaults.update(kwargs)
        return BacklogItem.objects.create(project=project, title=title, **defaults)

    def create_comment(self, item, author=None, from_stage='BACKLOG',
                       to_stage='SPRINT', body='Test comment'):
        author = author or self.pm_user
        return StageComment.objects.create(
            item=item, author_id=author.id,
            from_stage=from_stage, to_stage=to_stage, body=body,
        )


class MultiDBTransactionTestCase(TransactionTestCase):
    """Same idea as above, but for tests that need real DB commits
    (like LiveServerTestCase)."""

    databases = '__all__'

    def setUp(self):
        self.pm_user = User.objects.create_user(
            username='pm_user', email='pm@company.com', password='Test@1234!'
        )
        self.dev_user = User.objects.create_user(
            username='dev_user', email='dev@company.com', password='DevPass@123'
        )
        self.client = Client()
        self.factory = RequestFactory()

    def login_as_pm(self):
        self.client.login(username='pm_user', password='Test@1234!')

    def create_project(self, owner=None, name='Test Project', **kwargs):
        owner = owner or self.pm_user
        return Project.objects.create(name=name, owner_id=owner.id, **kwargs)

    def create_sprint(self, project, name='Sprint 1', status='PLANNING', **kwargs):
        return Sprint.objects.create(
            project=project, name=name, status=status, **kwargs
        )

    def create_item(self, project, title='Test Task', creator=None, **kwargs):
        creator = creator or self.pm_user
        defaults = {
            'status': 'BACKLOG',
            'priority': 'MED',
            'created_by_id': creator.id,
        }
        defaults.update(kwargs)
        return BacklogItem.objects.create(project=project, title=title, **defaults)
