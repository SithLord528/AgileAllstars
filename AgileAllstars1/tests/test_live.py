"""
LiveServerTestCase - End-to-End HTTP Tests

Spins up an actual HTTP server and hits pages to make sure
everything is wired up and reachable.

NOTE: The status transition URL changed from /item/<id>/move/<status>/
to /item/<id>/status/<status>/.
"""

import urllib.request
import urllib.error

from django.test import LiveServerTestCase
from django.contrib.auth.models import User

from sprints.models import Project, Sprint, BacklogItem


class LiveServerSmokeTests(LiveServerTestCase):
    """Basic smoke tests — can we even reach the login and register pages?"""

    databases = '__all__'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pm_user = User.objects.create_user(
            username='live_pm', email='live@company.com', password='LiveTest@1!'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def _get(self, path):
        """Helper to hit a path on the live server and return (status, body)."""
        url = f'{self.live_server_url}{path}'
        try:
            resp = urllib.request.urlopen(url)
            return resp.status, resp.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()

    def test_login_page_is_reachable(self):
        status, body = self._get('/login/')
        self.assertEqual(status, 200)
        self.assertIn('login', body.lower())

    def test_register_page_is_reachable(self):
        status, body = self._get('/register/')
        self.assertEqual(status, 200)

    def test_unauthenticated_root_redirects(self):
        """Hit the root URL without logging in — should bounce to login."""
        url = f'{self.live_server_url}/'
        req = urllib.request.Request(url)
        try:
            opener = urllib.request.build_opener(
                urllib.request.HTTPRedirectHandler
            )
            resp = opener.open(req)
            self.assertIn('login', resp.url)
        except urllib.error.HTTPError as e:
            self.assertIn(e.code, (301, 302))


class LiveServerAuthenticatedTests(LiveServerTestCase):
    """Log in with Django's test client and walk through some real workflows."""

    databases = '__all__'

    def setUp(self):
        self.user = User.objects.create_user(
            username='live_pm2', email='live2@company.com', password='LiveTest@2!'
        )
        self.client.login(username='live_pm2', password='LiveTest@2!')

    def test_login_and_access_dashboard(self):
        """After logging in, the dashboard (project list) should load fine."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_create_project_and_view_board(self):
        """Create a project, then go to its board page."""
        response = self.client.post('/', {
            'name': 'Live Project', 'description': '',
        })
        project = Project.objects.get(name='Live Project')
        response = self.client.get(f'/project/{project.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Live Project')

    def test_full_sprint_workflow(self):
        """Walk through the whole thing: create project -> add sprint ->
        activate -> add item -> move BACKLOG -> SPRINT -> TEST -> DONE."""
        # 1. Create the project
        self.client.post('/', {'name': 'Workflow Proj', 'description': ''})
        project = Project.objects.get(name='Workflow Proj')

        # 2. Add a sprint
        self.client.post(
            f'/project/{project.id}/add-sprint/',
            {'name': 'Sprint Live', 'goal': ''},
        )
        sprint = Sprint.objects.get(name='Sprint Live')

        # 3. Activate it
        self.client.post(f'/sprint/{sprint.id}/activate/')
        sprint.refresh_from_db()
        self.assertEqual(sprint.status, 'ACTIVE')

        # 4. Add a backlog item
        self.client.post(
            f'/project/{project.id}/add-item/',
            {'title': 'Live Item', 'description': '', 'priority': 'MED'},
        )
        item = BacklogItem.objects.get(title='Live Item')
        self.assertEqual(item.status, 'BACKLOG')

        # 5. Move it through the board
        # URL changed from /move/ to /status/
        self.client.post(f'/item/{item.id}/status/SPRINT/', {'comment': ''})
        item.refresh_from_db()
        self.assertEqual(item.status, 'SPRINT')

        self.client.post(f'/item/{item.id}/status/TEST/', {'comment': 'Ready'})
        item.refresh_from_db()
        self.assertEqual(item.status, 'TEST')

        self.client.post(f'/item/{item.id}/status/DONE/', {'comment': 'Passed'})
        item.refresh_from_db()
        self.assertEqual(item.status, 'DONE')
