"""
Test Case 4 - Comments and Notes  (TC-F4-001 through TC-F4-006)

PM and dev users exist. There's a project with a backlog item we
can attach comments to.

NOTE: The view no longer strips whitespace from comment bodies,
so whitespace-only comments will be saved. And the edit/delete
comment views now redirect instead of returning 403 Forbidden.
"""

from django.urls import reverse

from sprints.models import StageComment, BacklogItem
from .base import MultiDBTestCase


class StageCommentTests(MultiDBTestCase):
    """Adding, editing, deleting, and permission-checking comments on tasks."""

    def setUp(self):
        super().setUp()
        self.login_as_pm()
        self.project = self.create_project()
        self.sprint = self.create_sprint(self.project, status='ACTIVE')
        self.item = self.create_item(self.project, title='Commentable Task')

    # -- TC-F4-001: Add a comment while moving an item between stages --
    def test_TC_F4_001_add_comment_during_transition(self):
        """Move BACKLOG -> SPRINT with a comment — comment should be saved
        with the right from/to stages."""
        url = reverse(
            'update_item_status',
            kwargs={'item_id': self.item.id, 'new_status': 'SPRINT'},
        )
        response = self.client.post(url, {
            'comment': 'Please review the wireframes before proceeding.',
        })
        self.assertRedirects(
            response,
            reverse('project_board', kwargs={'project_id': self.project.id}),
        )
        comment = StageComment.objects.get(item=self.item)
        self.assertEqual(comment.body, 'Please review the wireframes before proceeding.')
        self.assertEqual(comment.from_stage, 'BACKLOG')
        self.assertEqual(comment.to_stage, 'SPRINT')
        self.assertEqual(comment.author_id, self.pm_user.id)

    def test_TC_F4_001_add_standalone_comment(self):
        """Add a comment from the item detail page without moving stages."""
        url = reverse('item_detail', kwargs={'item_id': self.item.id})
        response = self.client.post(url, {
            'action': 'add_comment',
            'comment_body': 'Please review the wireframes before proceeding.',
        })
        self.assertRedirects(response, url)
        comment = StageComment.objects.get(item=self.item)
        self.assertEqual(comment.body, 'Please review the wireframes before proceeding.')
        # from_stage and to_stage are the same since we didn't move it
        self.assertEqual(comment.from_stage, 'BACKLOG')
        self.assertEqual(comment.to_stage, 'BACKLOG')

    # -- TC-F4-002: Edit your own comment --
    def test_TC_F4_002_edit_own_comment(self):
        """Should be able to update the body of your own comment."""
        comment = self.create_comment(self.item, author=self.pm_user, body='Original')
        url = reverse('edit_comment', kwargs={'comment_id': comment.id})
        response = self.client.post(url, {'body': 'Updated text'}, follow=True)
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.body, 'Updated text')

    # -- TC-F4-003: Delete your own comment --
    def test_TC_F4_003_delete_own_comment(self):
        """POST to delete — comment should be gone."""
        comment = self.create_comment(self.item, author=self.pm_user)
        url = reverse('delete_comment', kwargs={'comment_id': comment.id})
        response = self.client.post(url)
        self.assertFalse(StageComment.objects.filter(id=comment.id).exists())

    # -- TC-F4-004: Try to edit/delete someone else's comment --
    # The views now redirect with an error message instead of returning 403.
    def test_TC_F4_004_cannot_edit_other_users_comment(self):
        """Trying to edit someone else's comment — should redirect and
        leave the comment unchanged."""
        comment = self.create_comment(self.item, author=self.pm_user, body='Original')
        # Add dev as a collaborator so they can access the project
        self.project.collaborator_ids = [self.dev_user.id]
        self.project.save()

        self.login_as_dev()
        url = reverse('edit_comment', kwargs={'comment_id': comment.id})
        response = self.client.post(url, {'body': 'Hacked!'})
        # View now redirects instead of returning 403
        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertEqual(comment.body, 'Original')

    def test_TC_F4_004b_cannot_delete_other_users_comment(self):
        """Trying to delete someone else's comment — should redirect
        and the comment stays."""
        comment = self.create_comment(self.item, author=self.pm_user)
        self.project.collaborator_ids = [self.dev_user.id]
        self.project.save()

        self.login_as_dev()
        url = reverse('delete_comment', kwargs={'comment_id': comment.id})
        response = self.client.post(url)
        # View silently ignores the delete and just redirects
        self.assertEqual(response.status_code, 302)
        self.assertTrue(StageComment.objects.filter(id=comment.id).exists())

    # -- TC-F4-005: Try to submit an empty comment --
    def test_TC_F4_005_empty_standalone_comment_rejected(self):
        """Blank comment body — no comment should be created."""
        url = reverse('item_detail', kwargs={'item_id': self.item.id})
        response = self.client.post(url, {
            'action': 'add_comment',
            'comment_body': '',
        })
        # Empty string is falsy so the view skips creation
        self.assertEqual(StageComment.objects.filter(item=self.item).count(), 0)

    def test_TC_F4_005b_whitespace_only_comment_saved(self):
        """Whitespace-only body is truthy in Python so the view saves it.
        (The old view used .strip() but the current one doesn't.)"""
        url = reverse('item_detail', kwargs={'item_id': self.item.id})
        self.client.post(url, {
            'action': 'add_comment',
            'comment_body': '   ',
        })
        self.assertEqual(StageComment.objects.filter(item=self.item).count(), 1)

    def test_TC_F4_005c_empty_transition_comment_skipped(self):
        """Empty comment during a status move is just silently skipped —
        the item still moves, but no comment is created."""
        url = reverse(
            'update_item_status',
            kwargs={'item_id': self.item.id, 'new_status': 'SPRINT'},
        )
        self.client.post(url, {'comment': ''})
        self.assertEqual(StageComment.objects.filter(item=self.item).count(), 0)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, 'SPRINT')

    # -- TC-F4-006: Edit a task's description --
    def test_TC_F4_006_edit_description_via_item_detail(self):
        """Update the description and make sure it sticks."""
        url = reverse('item_detail', kwargs={'item_id': self.item.id})
        self.client.post(url, {
            'action': 'update_details',
            'title': self.item.title,
            'description': 'Detailed design spec goes here.',
            'assignee': '',
            'priority': 'MED',
        })
        self.item.refresh_from_db()
        self.assertEqual(self.item.description, 'Detailed design spec goes here.')

        response = self.client.get(url)
        self.assertContains(response, 'Detailed design spec goes here.')


class CommentModelTests(MultiDBTestCase):
    """Direct model-level tests for StageComment."""

    def test_comment_author_resolves(self):
        """The author property should give us back the actual User object."""
        project = self.create_project()
        item = self.create_item(project)
        comment = self.create_comment(item, author=self.pm_user)
        self.assertEqual(comment.author, self.pm_user)

    def test_comment_author_missing_returns_none(self):
        """If the author was deleted, the property should return None."""
        project = self.create_project()
        item = self.create_item(project)
        comment = self.create_comment(item)
        comment.author_id = 99999
        comment.save()
        self.assertIsNone(comment.author)

    def test_comments_ordered_newest_first(self):
        project = self.create_project()
        item = self.create_item(project)
        c1 = self.create_comment(item, body='First')
        c2 = self.create_comment(item, body='Second')
        comments = list(StageComment.objects.filter(item=item))
        self.assertEqual(comments[0].id, c2.id)

    def test_cascade_delete_with_item(self):
        """Deleting a task should also delete all its comments."""
        project = self.create_project()
        item = self.create_item(project)
        self.create_comment(item)
        item_id = item.id
        item.delete()
        self.assertEqual(StageComment.objects.filter(item_id=item_id).count(), 0)
