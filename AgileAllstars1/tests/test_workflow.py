"""
Workflow and Status Transition Tests

Tests the Agile board status changes:

    BACKLOG -> SPRINT -> TEST -> DONE
                ^         |       |
                |         v       v
                +-- (fail/rework) |
                                  +-> BACKLOG (re-open)

NOTE: The current update_item_status view does NOT validate transitions
via can_transition_to(). Any valid status value is accepted. It also no
longer assigns the sprint or checks for an active sprint when moving
BACKLOG -> SPRINT. The tests below reflect the current behavior.
"""

from django.urls import reverse

from sprints.models import BacklogItem, Sprint, StageComment
from .base import MultiDBTestCase


class ValidTransitionTests(MultiDBTestCase):
    """Make sure status moves on the board actually work."""

    def setUp(self):
        super().setUp()
        self.login_as_pm()
        self.project = self.create_project()
        self.sprint = self.create_sprint(self.project, status='ACTIVE')

    def _move(self, item, new_status):
        """Helper to POST a status transition."""
        url = reverse(
            'update_item_status',
            kwargs={'item_id': item.id, 'new_status': new_status},
        )
        return self.client.post(url, {'comment': ''})

    def test_backlog_to_sprint(self):
        item = self.create_item(self.project, status='BACKLOG')
        self._move(item, 'SPRINT')
        item.refresh_from_db()
        self.assertEqual(item.status, 'SPRINT')
        # Sprint assignment no longer happens in the view
        self.assertIsNone(item.sprint)

    def test_sprint_to_test(self):
        item = self.create_item(self.project, status='SPRINT', sprint=self.sprint)
        self._move(item, 'TEST')
        item.refresh_from_db()
        self.assertEqual(item.status, 'TEST')

    def test_test_to_done(self):
        item = self.create_item(self.project, status='TEST', sprint=self.sprint)
        self._move(item, 'DONE')
        item.refresh_from_db()
        self.assertEqual(item.status, 'DONE')

    def test_test_to_sprint_rework(self):
        """Failed test — send it back to Sprint Backlog for another round."""
        item = self.create_item(self.project, status='TEST', sprint=self.sprint)
        self._move(item, 'SPRINT')
        item.refresh_from_db()
        self.assertEqual(item.status, 'SPRINT')

    def test_sprint_to_backlog_demote(self):
        item = self.create_item(self.project, status='SPRINT', sprint=self.sprint)
        self._move(item, 'BACKLOG')
        item.refresh_from_db()
        self.assertEqual(item.status, 'BACKLOG')

    def test_done_to_backlog_reopen(self):
        item = self.create_item(self.project, status='DONE')
        self._move(item, 'BACKLOG')
        item.refresh_from_db()
        self.assertEqual(item.status, 'BACKLOG')

    def test_full_lifecycle(self):
        """Happy path: BACKLOG -> SPRINT -> TEST -> DONE all in one go."""
        item = self.create_item(self.project)
        for status in ('SPRINT', 'TEST', 'DONE'):
            self._move(item, status)
            item.refresh_from_db()
            self.assertEqual(item.status, status)


class UnvalidatedTransitionTests(MultiDBTestCase):
    """The view currently doesn't enforce can_transition_to(), so
    any valid status value is accepted regardless of the current state.
    These tests document that behavior."""

    def setUp(self):
        super().setUp()
        self.login_as_pm()
        self.project = self.create_project()
        self.sprint = self.create_sprint(self.project, status='ACTIVE')

    def _move(self, item, new_status):
        url = reverse(
            'update_item_status',
            kwargs={'item_id': item.id, 'new_status': new_status},
        )
        return self.client.post(url, {'comment': ''})

    def test_backlog_to_test_accepted(self):
        """Normally invalid, but the view allows it right now."""
        item = self.create_item(self.project, status='BACKLOG')
        self._move(item, 'TEST')
        item.refresh_from_db()
        self.assertEqual(item.status, 'TEST')

    def test_backlog_to_done_accepted(self):
        item = self.create_item(self.project, status='BACKLOG', title='Skip to done')
        self._move(item, 'DONE')
        item.refresh_from_db()
        self.assertEqual(item.status, 'DONE')

    def test_done_to_sprint_accepted(self):
        item = self.create_item(self.project, status='DONE', title='Done to sprint')
        self._move(item, 'SPRINT')
        item.refresh_from_db()
        self.assertEqual(item.status, 'SPRINT')

    def test_done_to_test_accepted(self):
        item = self.create_item(self.project, status='DONE', title='Done to test')
        self._move(item, 'TEST')
        item.refresh_from_db()
        self.assertEqual(item.status, 'TEST')

    def test_sprint_to_done_accepted(self):
        """Skipping TEST — the view allows it."""
        item = self.create_item(self.project, status='SPRINT', sprint=self.sprint)
        self._move(item, 'DONE')
        item.refresh_from_db()
        self.assertEqual(item.status, 'DONE')

    def test_bogus_status_rejected(self):
        """A completely made-up status IS still rejected by the view."""
        item = self.create_item(self.project, status='BACKLOG', title='Bogus test')
        self._move(item, 'NONEXISTENT')
        item.refresh_from_db()
        self.assertEqual(item.status, 'BACKLOG')


class TransitionSprintBehaviorTests(MultiDBTestCase):
    """The view no longer checks for an active sprint or assigns the
    sprint when moving BACKLOG -> SPRINT."""

    def setUp(self):
        super().setUp()
        self.login_as_pm()
        self.project = self.create_project()

    def test_backlog_to_sprint_without_active_sprint(self):
        """No active sprint — move still goes through now."""
        self.create_sprint(self.project, status='PLANNING')
        item = self.create_item(self.project, status='BACKLOG')
        url = reverse(
            'update_item_status',
            kwargs={'item_id': item.id, 'new_status': 'SPRINT'},
        )
        self.client.post(url, {'comment': ''})
        item.refresh_from_db()
        self.assertEqual(item.status, 'SPRINT')

    def test_backlog_to_sprint_does_not_assign_sprint(self):
        """Even with an active sprint, the view doesn't assign it anymore."""
        sprint = self.create_sprint(self.project, status='ACTIVE')
        item = self.create_item(self.project, status='BACKLOG')
        url = reverse(
            'update_item_status',
            kwargs={'item_id': item.id, 'new_status': 'SPRINT'},
        )
        self.client.post(url, {'comment': ''})
        item.refresh_from_db()
        self.assertEqual(item.status, 'SPRINT')
        self.assertIsNone(item.sprint)


class TransitionCommentTests(MultiDBTestCase):
    """Make sure comments get attached correctly when moving items."""

    def setUp(self):
        super().setUp()
        self.login_as_pm()
        self.project = self.create_project()
        self.sprint = self.create_sprint(self.project, status='ACTIVE')

    def test_comment_recorded_on_transition(self):
        item = self.create_item(self.project, status='BACKLOG')
        url = reverse(
            'update_item_status',
            kwargs={'item_id': item.id, 'new_status': 'SPRINT'},
        )
        self.client.post(url, {'comment': 'Moving to sprint for iteration 1'})
        comment = StageComment.objects.get(item=item)
        self.assertEqual(comment.from_stage, 'BACKLOG')
        self.assertEqual(comment.to_stage, 'SPRINT')
        self.assertEqual(comment.body, 'Moving to sprint for iteration 1')

    def test_no_comment_when_field_empty(self):
        item = self.create_item(self.project, status='BACKLOG')
        url = reverse(
            'update_item_status',
            kwargs={'item_id': item.id, 'new_status': 'SPRINT'},
        )
        self.client.post(url, {'comment': ''})
        self.assertEqual(StageComment.objects.filter(item=item).count(), 0)

    def test_transition_page_renders_on_get(self):
        """GET the transition URL — should show us the comment form."""
        item = self.create_item(self.project, status='BACKLOG')
        url = reverse(
            'update_item_status',
            kwargs={'item_id': item.id, 'new_status': 'SPRINT'},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
