# Known Issues, Defects & Technical Debt

> Last updated: 2026-04-16

This document provides an honest disclosure of outstanding defects and gaps
between the spreadsheet test-case requirements and the current implementation.

---

## Resolved Security Issues

| ID | Category | Description | Resolution |
|----|----------|-------------|------------|
| SEC-001 | **Missing Auth** | `invite_collaborator` was missing `@login_required`. | **Resolved** -- Decorator added. Verified by `test_invite_collaborator_requires_login`. |
| SEC-002 | **No Membership Check** | Any authenticated user could view/modify any project. | **Resolved** -- `_require_membership()` helper added to all project-scoped views. `project_list` now filters to owned/collaborated projects only. Verified by 12 new `MembershipEnforcementTests`. |

## Remaining Security Items

| ID | Category | Description | Status |
|----|----------|-------------|--------|
| SEC-003 | **Secret Key in Repo** | `settings.py` contains a hard-coded insecure `SECRET_KEY`. Must be moved to an environment variable before production. | **Open** |
| SEC-004 | **DEBUG = True** | `DEBUG` is set to `True` in `settings.py`. Must be `False` in production. | **Open** |

---

## Resolved Feature Gaps

All spreadsheet test-case requirements are now implemented and verified by
passing tests (172 total, 0 expected failures).

| Test Case ID | Requirement | Resolution |
|--------------|-------------|------------|
| **F1-005** | Account lockout after 5 failed login attempts | Implemented via Django cache-based rate limiter in `sign_in()`. After 5 failures the user sees "Too many failed attempts. Try again in 15 minutes." Verified by `test_F1_005_*` (3 tests). |
| **F2-004** | Reject duplicate project names | `Project.name` now has `unique=True` (migration `0003`). `ProjectForm` automatically shows a validation error. Verified by `test_F2_004_duplicate_name_rejected`. |
| **F3-002** | Edit task title and description via UI | `item_detail` POST now accepts `title` and `description` fields. Template updated with editable inputs. Verified by `test_F3_002_edit_task_title_and_description`. |
| **F3-005** | Validate end date is not before start date | `start_date` and `end_date` fields added to `BacklogItem` (migration `0003`). `BacklogItemForm.clean()` raises `ValidationError` when `end_date < start_date`. Verified by `test_F3_005_*` (2 tests). |
| **TC-F4-002** | Edit own comment | `edit_comment` view added at `/comment/<id>/edit/` with ownership check. Verified by `test_TC_F4_002_edit_own_comment`. |
| **TC-F4-003** | Delete own comment | `delete_comment` view added at `/comment/<id>/delete/` with ownership check. Verified by `test_TC_F4_003_delete_own_comment`. |
| **TC-F4-004** | Prevent editing/deleting another user's comment | Both `edit_comment` and `delete_comment` return `403 Forbidden` when `request.user.id != comment.author_id`. Verified by `test_TC_F4_004_*` (2 tests). |
| **TC-F4-005** | Reject empty comments with an error message | Standalone "Add Comment" form on `item_detail` validates non-empty body and shows "Comment cannot be empty." error. Verified by `test_TC_F4_005_*` (3 tests). |

---

## Technical Debt

| Area | Description | Priority |
|------|-------------|----------|
| **Legacy `Task` model** | `taskStatus.Task` model is defined and migrated but not used by any view. All active functionality uses `sprints.BacklogItem`. Consider removing it. | Low |
| **Multi-DB Complexity** | Cross-database references (user IDs stored as integers) prevent Django ORM joins. Consider consolidating to a single database if cross-DB is not required. | Medium |
| **Apps `ready()` Auto-Migration** | `UsersConfig.ready()` and `SprintsConfig.ready()` call `manage.py migrate` at startup if the DB file is missing. Skipped during `test`/`migrate`/`makemigrations` but the pattern is fragile. | Medium |
| **`InviteCollaboratorForm` Unused** | `sprints/forms.py` defines `InviteCollaboratorForm` but the view reads `request.POST` directly. | Low |
| **No Pagination** | Project list and backlog items have no pagination. | Low |
| **STATIC_ROOT Not Set** | `settings.py` has no `STATIC_ROOT`, required for `collectstatic` in production. | Medium |
| **Priority Ordering** | `BacklogItem.Meta.ordering = ['-priority']` sorts alphabetically on stored string values (`CRIT < HIGH < LOW < MED`), which does not match semantic priority. Consider using `IntegerField` or a custom sort key. | Low |
| **Login Lockout Persistence** | The login lockout uses Django's in-process `LocMemCache`, which resets on server restart. For production, configure Redis or Memcached to persist lockout state across restarts. | Medium |

---

## Tests Marked as `expectedFailure`

**None.** All spreadsheet requirements are now implemented and tested.

---

## Test Suite Summary

| Category | Count |
|----------|-------|
| Total tests | 172 |
| Passing | 172 |
| Expected failures | 0 |
| Skipped | 0 |
| Test modules | 9 |

### Test Frameworks Used

- `django.test.TestCase` -- Standard transactional tests
- `django.test.TransactionTestCase` -- Multi-DB transaction tests
- `django.test.LiveServerTestCase` -- Full HTTP server smoke tests
- `django.test.RequestFactory` -- Low-level view unit tests
- `django.test.Client` -- HTTP-level integration tests (with CSRF enforcement variant)
- Django cache (`LocMemCache`) -- Lockout feature testing
