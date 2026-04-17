# Agile Projects Database — Commit Statement, Change Log, and Implementation Guide

## 1. Commit Statement

```
Add separate projects database, Agile sprint/backlog models, and wire
board UI to new data layer

- New 'sprints' app with Project, Sprint, and BacklogItem models in a
  dedicated agile_projects.sqlite3 database, with auto-init on startup.
- Database router (AgileDBRouter) enforces separation: auth/session data
  stays in agile_auth.sqlite3, project data in agile_projects.sqlite3.
- Renamed db.sqlite3 -> agile_auth.sqlite3 with auto-rename fallback.
- Rewired taskStatus as presentation layer: views, forms, URLs, and
  templates now import from sprints.models instead of the old Task model.
- Board template updated with Agile columns (Product Backlog, Sprint
  Backlog, Ready for Test, Complete), priority badges, sprint management
  panel, completion progress bars, and POST forms for all state changes.
- Added project list page at / with project creation and completion
  overview.
- Updated base.html with nav links, title block, and extra_head block.
- Fixed NoReverseMatch crash (redirect to nonexistent 'posts' URL) and
  added @login_required to logout view.
```

---

## 2. Detailed Guide: What Changed

### New Files

| File | Purpose |
|---|---|
| `sprints/__init__.py` | Package init |
| `sprints/models.py` | **Project** (name, description, owner_id, completion_percentage, item_counts), **Sprint** (name, goal, status, date range, completion_percentage, item_counts), **BacklogItem** (title, description, status, priority, sprint FK, assigned_to_id, created_by_id, can_transition_to, valid transitions). All user references are IntegerFields with @property resolvers to avoid cross-database ForeignKeys. |
| `sprints/apps.py` | Auto-creates `agile_projects.sqlite3` on startup if missing, verifies connection otherwise. Mirrors the pattern in `users/apps.py`. |
| `sprints/admin.py` | Registers Project, Sprint, BacklogItem in Django admin with list_display, filters, and search. |
| `sprints/migrations/0001_initial.py` | Creates the three tables in the projects database. |
| `AgileAllstars/db_router.py` | Routes `sprints` app models to the `projects` database; everything else to `default`. Blocks cross-database relations. |
| `taskStatus/templates/taskStatus/project_list.html` | Project list page with creation form, project cards, and completion progress bars. |

### Modified Files

#### `AgileAllstars/settings.py`

- Default database renamed: `db.sqlite3` → `agile_auth.sqlite3`
- Added `projects` database: `agile_projects.sqlite3`
- Added `DATABASE_ROUTERS` pointing to `AgileDBRouter`
- Added `sprints.apps.SprintsConfig` to `INSTALLED_APPS`

#### `users/apps.py`

- Auto-renames old `db.sqlite3` to `agile_auth.sqlite3` on first startup
- Falls back to running `migrate` only if neither file exists

#### `users/views.py`

- `sign_in`: fixed `redirect('posts')` → `redirect('project_list')` (was a crash)
- `sign_out`: added `@login_required` decorator
- Added `login_required` import

#### `users/templates/base.html`

- Added `{% block title %}` and `{% block extra_head %}` blocks
- Added "Projects" nav link for authenticated users
- Added "Register" link for unauthenticated users
- Fixed a quoting bug in the message alert `class` attribute

#### `taskStatus/views.py`

Complete rewrite. Now imports from `sprints.models` instead of `taskStatus.models`:

| View | URL | What it does |
|---|---|---|
| `project_list` | `/` | Lists projects, POST creates a new one |
| `project_board` | `/project/<id>/` | Renders the Agile board for a project |
| `create_item` | `/project/<id>/add-item/` | Adds a BacklogItem to Product Backlog |
| `create_sprint` | `/project/<id>/add-sprint/` | Creates a Sprint in Planning status |
| `activate_sprint` | `/sprint/<id>/activate/` | Sets sprint to Active, closes any prior active sprint |
| `close_sprint` | `/sprint/<id>/close/` | Sets sprint to Closed |
| `update_item_status` | `/item/<id>/move/<status>/` | Enforces `can_transition_to()`, assigns sprint on Backlog→Sprint |
| `update_item_priority` | `/item/<id>/priority/<priority>/` | Changes priority |

All views require `@login_required`. All state-changing views require POST.

#### `taskStatus/forms.py`

Three new ModelForms replacing the old `TaskForm`:

- `ProjectForm` (name, description)
- `SprintForm` (name, goal, start_date, end_date — uses HTML5 date inputs)
- `BacklogItemForm` (title, description, priority — status is not exposed; items always start in Product Backlog)

#### `taskStatus/urls.py`

Replaced the old three-route pattern with eight routes matching the view table above.

#### `taskStatus/templates/taskStatus/taskBoard.html`

Rewritten to:

- Extend `base.html` (shared header, nav, messages)
- Show project name with completion progress bar
- Sprint management panel (active sprint with close button, planning sprints with activate buttons, collapsible "New Sprint" form)
- Four Agile columns: Product Backlog, Sprint Backlog, Ready for Test, Complete
- Color-coded priority badges (red/orange/blue/gray)
- POST forms for every state change (CSRF-protected)
- Pass/Fail buttons in the Ready for Test column
- "Move to Sprint" gated on having an active sprint
- Description previews and timestamps on cards

### Architecture After This Change

```
users app           taskStatus app           sprints app
(auth layer)        (presentation layer)     (data layer)
     │                     │                      │
     │  login/logout       │  views, forms,       │  models only
     │  register           │  URLs, templates     │  (no views)
     │  session mgmt       │                      │
     │                     │  imports from ────────┤
     ▼                     ▼                      ▼
agile_auth.sqlite3                        agile_projects.sqlite3
  auth_user                                 sprints_project
  auth_group         ◄── router ──►         sprints_sprint
  django_session                            sprints_backlogitem
  taskStatus_task (legacy, unused)
```

### Dead Code

- `taskStatus/models.py` — the old `Task` model is no longer used by any view. It remains in the auth database's `taskStatus_task` table but nothing reads or writes to it. Can be removed in a future cleanup.

---

## 3. Implementation Guide: What Remains for the Dev Team

The core system is functional. Below are enhancements and cleanup tasks organized by priority.

### High Priority

#### 3.1 — Remove the Legacy Task Model

Delete the `Task` class from `taskStatus/models.py` and create a migration to drop the `taskStatus_task` table from the auth database. This avoids confusion about which model is the source of truth.

```bash
# After deleting the Task class from taskStatus/models.py:
python3 manage.py makemigrations taskStatus
python3 manage.py migrate
```

#### 3.2 — Respect Django's `next` Parameter After Login

Currently `sign_in` always redirects to `project_list` after login. If a user was redirected to login by `@login_required` (e.g., they tried to access `/project/3/`), they should land back on that page. Update the POST handler in `users/views.py`:

```python
next_url = request.POST.get('next') or request.GET.get('next') or 'project_list'
return redirect(next_url)
```

And in `login.html`, add a hidden field:

```html
<input type="hidden" name="next" value="{{ request.GET.next }}" />
```

#### 3.3 — Scope Project Visibility

Currently all authenticated users can see all projects. For team-based access control, add a `members` field to `Project` (as an `IntegerField`-based through table, or a simple comma-separated list of user IDs). Then filter `project_list` to only show projects the user owns or is a member of, and add permission checks in `project_board`.

### Medium Priority

#### 3.4 — Task Assignment

`BacklogItem.assigned_to_id` exists but there's no UI to set it. Add an "Assign" dropdown to the board cards or the item creation form. To populate the dropdown, query users from the auth database:

```python
from django.contrib.auth.models import User
users = User.objects.using('default').values_list('id', 'username')
```

Pass this as choices to a form field, or render it directly in the template.

#### 3.5 — Sprint Velocity and Burndown Data

The `completion_percentage` and `item_counts` properties provide the raw data. To build a burndown chart:

- Record daily snapshots of `sprint.item_counts` (requires a new `SprintSnapshot` model or a cron job writing to a JSON field)
- Render with a JavaScript charting library (Chart.js is lightweight and works well)

#### 3.6 — Password Management

Django provides built-in views for password change and reset. Wire them into `users/urls.py`:

```python
from django.contrib.auth import views as auth_views

urlpatterns += [
    path('password-change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
]
```

### Low Priority / Polish

#### 3.7 — Drag-and-Drop on the Board

The current board uses button clicks for transitions. For a more fluid UX, add JavaScript drag-and-drop using the HTML5 Drag and Drop API or a library like SortableJS. Each drop would submit a POST to `update_item_status`.

#### 3.8 — Item Detail/Edit Page

Currently there's no way to edit an item's title, description, or view its full details after creation. Add an item detail view at `/item/<id>/` with an edit form.

#### 3.9 — Closed Sprint Archive

Add a view to list closed sprints for a project, showing their final completion stats and which items they contained. This supports retrospectives.

#### 3.10 — Tests

Both `taskStatus/tests.py` and `sprints/tests.py` are empty. Key test cases:

- Workflow transitions (valid and invalid)
- Sprint activation closes prior active sprint
- Backlog-to-Sprint blocked when no active sprint exists
- Unauthenticated access is redirected
- Completion percentages with zero items, partial completion, and full completion
- Database routing (sprints models write to projects DB, auth models write to default DB)
