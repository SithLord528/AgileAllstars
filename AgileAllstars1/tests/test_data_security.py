"""
Data Security and Access Control Tests

Makes sure that:
- You can't hit any protected page without logging in first
- project_board blocks non-members (only view with membership check)
- Only the owner can delete projects
- CSRF tokens are enforced
- The DB router sends models to the right database

NOTE: Most membership checks were removed in recent codebase changes.
Only project_board still enforces membership. The invite_collaborator
view no longer has an owner-only check. These regressions are
documented here so we know the current state.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from sprints.models import Project, BacklogItem
from .base import MultiDBTestCase


# ======================================================================
#  Authentication — every @login_required view should bounce you to login
# ======================================================================

class AuthenticationEnforcementTests(MultiDBTestCase):
    """Try to hit every protected view while logged out.
    All of them should redirect us to /login/."""

    def _assert_login_redirect(self, url, method='get'):
        fn = getattr(self.client, method)
        response = fn(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_project_list_requires_login(self):
        self._assert_login_redirect(reverse('project_list'))

    def test_project_board_requires_login(self):
        project = self.create_project()
        self._assert_login_redirect(
            reverse('project_board', kwargs={'project_id': project.id})
        )

    def test_create_item_requires_login(self):
        project = self.create_project()
        self._assert_login_redirect(
            reverse('create_item', kwargs={'project_id': project.id}), method='post'
        )

    def test_create_sprint_requires_login(self):
        project = self.create_project()
        self._assert_login_redirect(
            reverse('create_sprint', kwargs={'project_id': project.id}), method='post'
        )

    def test_activate_sprint_requires_login(self):
        project = self.create_project()
        sprint = self.create_sprint(project)
        self._assert_login_redirect(
            reverse('activate_sprint', kwargs={'sprint_id': sprint.id}), method='post'
        )

    def test_close_sprint_requires_login(self):
        project = self.create_project()
        sprint = self.create_sprint(project)
        self._assert_login_redirect(
            reverse('close_sprint', kwargs={'sprint_id': sprint.id}), method='post'
        )

    def test_update_item_status_requires_login(self):
        project = self.create_project()
        item = self.create_item(project)
        self._assert_login_redirect(
            reverse('update_item_status', kwargs={
                'item_id': item.id, 'new_status': 'SPRINT',
            }), method='post'
        )

    def test_item_detail_requires_login(self):
        project = self.create_project()
        item = self.create_item(project)
        self._assert_login_redirect(
            reverse('item_detail', kwargs={'item_id': item.id})
        )

    def test_delete_project_requires_login(self):
        project = self.create_project()
        self._assert_login_redirect(
            reverse('delete_project', kwargs={'project_id': project.id}), method='post'
        )

    def test_delete_item_requires_login(self):
        project = self.create_project()
        item = self.create_item(project)
        self._assert_login_redirect(
            reverse('delete_item', kwargs={'item_id': item.id}), method='post'
        )

    def test_invite_collaborator_requires_login(self):
        project = self.create_project()
        self._assert_login_redirect(
            reverse('invite_collaborator', kwargs={'project_id': project.id}),
            method='post',
        )

    def test_edit_comment_requires_login(self):
        project = self.create_project()
        item = self.create_item(project)
        from .base import StageComment
        comment = StageComment.objects.create(
            item=item, author_id=self.pm_user.id,
            from_stage='BACKLOG', to_stage='SPRINT', body='test',
        )
        self._assert_login_redirect(
            reverse('edit_comment', kwargs={'comment_id': comment.id}), method='post'
        )

    def test_delete_comment_requires_login(self):
        project = self.create_project()
        item = self.create_item(project)
        from .base import StageComment
        comment = StageComment.objects.create(
            item=item, author_id=self.pm_user.id,
            from_stage='BACKLOG', to_stage='SPRINT', body='test',
        )
        self._assert_login_redirect(
            reverse('delete_comment', kwargs={'comment_id': comment.id}), method='post'
        )


# ======================================================================
#  Membership — only project_board still enforces this
# ======================================================================

class MembershipEnforcementTests(MultiDBTestCase):
    """project_board checks that you're an owner or collaborator.
    Other views no longer enforce membership."""

    def setUp(self):
        super().setUp()
        self.project = self.create_project(owner=self.pm_user)
        self.item = self.create_item(self.project)
        self.sprint = self.create_sprint(self.project)

    def test_non_member_cannot_view_board(self):
        """project_board still has a membership check."""
        self.login_as_dev2()
        url = reverse('project_board', kwargs={'project_id': self.project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_collaborator_can_view_board(self):
        self.project.collaborator_ids = [self.dev_user.id]
        self.project.save()
        self.login_as_dev()
        url = reverse('project_board', kwargs={'project_id': self.project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_non_member_can_view_item_detail(self):
        """item_detail no longer checks membership."""
        self.login_as_dev2()
        url = reverse('item_detail', kwargs={'item_id': self.item.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_non_member_can_delete_item(self):
        """delete_item no longer checks membership."""
        self.login_as_dev2()
        url = reverse('delete_item', kwargs={'item_id': self.item.id})
        self.client.post(url)
        self.assertFalse(BacklogItem.objects.filter(id=self.item.id).exists())

    def test_collaborator_can_create_item(self):
        self.project.collaborator_ids = [self.dev_user.id]
        self.project.save()
        self.login_as_dev()
        url = reverse('create_item', kwargs={'project_id': self.project.id})
        self.client.post(url, {'title': 'Collab Item', 'description': '', 'priority': 'MED'})
        self.assertTrue(BacklogItem.objects.filter(title='Collab Item').exists())


# ======================================================================
#  Owner-Only Actions
# ======================================================================

class OwnerOnlyActionTests(MultiDBTestCase):
    """Only the owner should be able to delete projects.
    invite_collaborator no longer has an owner check."""

    def test_non_owner_cannot_delete_project(self):
        """Non-member gets blocked by the owner check — project survives."""
        project = self.create_project(owner=self.pm_user)
        self.login_as_dev()
        url = reverse('delete_project', kwargs={'project_id': project.id})
        self.client.post(url)
        self.assertTrue(Project.objects.filter(id=project.id).exists())

    def test_collaborator_cannot_delete_project(self):
        """Collaborator is blocked by the owner check."""
        project = self.create_project(owner=self.pm_user)
        project.collaborator_ids = [self.dev_user.id]
        project.save()
        self.login_as_dev()
        url = reverse('delete_project', kwargs={'project_id': project.id})
        self.client.post(url)
        self.assertTrue(Project.objects.filter(id=project.id).exists())

    def test_owner_can_delete_project(self):
        project = self.create_project(owner=self.pm_user)
        self.login_as_pm()
        url = reverse('delete_project', kwargs={'project_id': project.id})
        self.client.post(url)
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_any_user_can_invite_collaborator(self):
        """invite_collaborator no longer has an owner check —
        any logged-in user can invite."""
        project = self.create_project(owner=self.pm_user)
        project.collaborator_ids = [self.dev_user.id]
        project.save()
        self.login_as_dev()
        url = reverse('invite_collaborator', kwargs={'project_id': project.id})
        self.client.post(url, {'email': 'dev2@company.com'})
        project.refresh_from_db()
        self.assertIn(self.dev_user2.id, project.collaborator_ids)

    def test_owner_can_invite_collaborator(self):
        project = self.create_project(owner=self.pm_user)
        self.login_as_pm()
        url = reverse('invite_collaborator', kwargs={'project_id': project.id})
        self.client.post(url, {'email': 'dev@company.com'})
        project.refresh_from_db()
        self.assertIn(self.dev_user.id, project.collaborator_ids)

    def test_invite_nonexistent_email(self):
        """Try to invite someone who doesn't have an account."""
        project = self.create_project(owner=self.pm_user)
        self.login_as_pm()
        url = reverse('invite_collaborator', kwargs={'project_id': project.id})
        self.client.post(url, {'email': 'nobody@nowhere.com'})
        project.refresh_from_db()
        self.assertEqual(project.collaborator_ids, [])

    def test_invite_same_user_twice_no_duplicate(self):
        """Inviting the same person again shouldn't add a duplicate."""
        project = self.create_project(owner=self.pm_user)
        self.login_as_pm()
        url = reverse('invite_collaborator', kwargs={'project_id': project.id})
        self.client.post(url, {'email': 'dev@company.com'})
        self.client.post(url, {'email': 'dev@company.com'})
        project.refresh_from_db()
        self.assertEqual(project.collaborator_ids.count(self.dev_user.id), 1)


# ======================================================================
#  CSRF — make sure the middleware is actually doing its job
# ======================================================================

class CSRFProtectionTests(MultiDBTestCase):
    """POST without a CSRF token should get rejected with a 403."""

    def test_login_post_without_csrf_rejected(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse('login'), {
            'username': 'pm_user', 'password': 'Test@1234!',
        })
        self.assertEqual(response.status_code, 403)

    def test_create_project_without_csrf_rejected(self):
        client = Client(enforce_csrf_checks=True)
        client.login(username='pm_user', password='Test@1234!')
        response = client.post(reverse('project_list'), {
            'name': 'CSRF Test', 'description': '',
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Project.objects.filter(name='CSRF Test').exists())


# ======================================================================
#  DB Router — make sure models end up in the right database
# ======================================================================

class DatabaseRouterTests(TestCase):
    """Check that the AgileDBRouter sends each model to the right DB."""

    databases = '__all__'

    def test_user_model_uses_default_db(self):
        from AgileAllstars.db_router import AgileDBRouter
        router = AgileDBRouter()
        self.assertEqual(router.db_for_read(User), 'default')
        self.assertEqual(router.db_for_write(User), 'default')

    def test_project_model_uses_projects_db(self):
        from AgileAllstars.db_router import AgileDBRouter
        router = AgileDBRouter()
        self.assertEqual(router.db_for_read(Project), 'projects')
        self.assertEqual(router.db_for_write(Project), 'projects')

    def test_cross_db_relation_denied(self):
        """User (default DB) and Project (projects DB) shouldn't be
        allowed to have a direct FK relationship."""
        from AgileAllstars.db_router import AgileDBRouter
        router = AgileDBRouter()
        user = User(pk=1)
        project = Project(pk=1)
        self.assertFalse(router.allow_relation(user, project))

    def test_same_db_relation_allowed(self):
        from AgileAllstars.db_router import AgileDBRouter
        router = AgileDBRouter()
        p1 = Project(pk=1)
        p2 = Project(pk=2)
        self.assertTrue(router.allow_relation(p1, p2))

    def test_allow_migrate_sprints_to_projects(self):
        from AgileAllstars.db_router import AgileDBRouter
        router = AgileDBRouter()
        self.assertTrue(router.allow_migrate('projects', 'sprints'))
        self.assertFalse(router.allow_migrate('default', 'sprints'))

    def test_allow_migrate_auth_to_default(self):
        from AgileAllstars.db_router import AgileDBRouter
        router = AgileDBRouter()
        self.assertTrue(router.allow_migrate('default', 'auth'))
        self.assertFalse(router.allow_migrate('projects', 'auth'))
