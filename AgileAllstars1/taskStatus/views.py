from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from sprints.models import Project, Sprint, BacklogItem, StageComment
from .forms import ProjectForm, SprintForm, BacklogItemForm
from django.contrib.auth.models import User


def _is_project_member(user, project):
    """Return True if *user* is the project owner or a listed collaborator."""
    return (
        user.id == project.owner_id
        or user.id in (project.collaborator_ids or [])
    )


def _require_membership(request, project):
    """If the user is not a project member, add an error message and return a
    redirect response.  Otherwise return ``None``."""
    if not _is_project_member(request.user, project):
        messages.error(request, "You don't have access to this project.")
        return redirect('project_list')
    return None

@login_required
def project_list(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner_id = request.user.id
            project.save()
            return redirect('project_board', project_id=project.id)
    else:
        form = ProjectForm()

    uid = request.user.id
    projects = [
        p for p in Project.objects.all()
        if p.owner_id == uid or uid in (p.collaborator_ids or [])
    ]

    context = {
        'projects': projects,
        'form': form,
    }
    return render(request, 'taskStatus/project_list.html', context)


@login_required
def project_board(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    denied = _require_membership(request, project)
    if denied:
        return denied

    active_sprint = project.active_sprint
    items = project.backlog_items.all()

    context = {
        'project': project,
        'active_sprint': active_sprint,
        'planning_sprints': project.sprints.filter(status=Sprint.Status.PLANNING),
        'backlog_items': items.filter(status='BACKLOG'),
        'sprint_items': items.filter(status='SPRINT'),
        'test_items': items.filter(status='TEST'),
        'complete_items': items.filter(status='DONE'),
        'completion': project.completion_percentage,
        'sprint_completion': active_sprint.completion_percentage if active_sprint else 0,
        'item_form': BacklogItemForm(),
        'sprint_form': SprintForm(),
    }
    return render(request, 'taskStatus/taskBoard.html', context)

@login_required
def create_item(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    denied = _require_membership(request, project)
    if denied:
        return denied

    if request.method == 'POST':
        form = BacklogItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.project = project
            item.created_by_id = request.user.id
            item.save()
            messages.success(request, f'"{item.title}" added to Product Backlog.')
        else:
            for error_list in form.errors.values():
                for error in error_list:
                    messages.error(request, error)
    return redirect('project_board', project_id=project_id)


@login_required
def item_detail(request, item_id):
    item = get_object_or_404(BacklogItem, id=item_id)
    project = item.project
    denied = _require_membership(request, project)
    if denied:
        return denied

    comments = item.transition_comments.all()

    valid_assignees = list(project.collaborators.all())
    if project.owner and project.owner not in valid_assignees:
        valid_assignees.insert(0, project.owner)

    if request.method == 'POST':
        action = request.POST.get('action', 'update_details')

        if action == 'add_comment':
            body = request.POST.get('comment_body', '').strip()
            if body:
                StageComment.objects.create(
                    item=item,
                    author_id=request.user.id,
                    from_stage=item.status,
                    to_stage=item.status,
                    body=body,
                )
                messages.success(request, "Comment added.")
            else:
                messages.error(request, "Comment cannot be empty.")
            return redirect('item_detail', item_id=item.id)

        new_title = request.POST.get('title', '').strip()
        if new_title:
            item.title = new_title

        item.description = request.POST.get('description', '')

        assignee_id = request.POST.get('assignee')
        if assignee_id:
            item.assigned_to_id = int(assignee_id)
        else:
            item.assigned_to_id = None

        new_priority = request.POST.get('priority')
        valid_priorities = [p[0] for p in BacklogItem.Priority.choices]
        if new_priority in valid_priorities:
            item.priority = new_priority

        item.save()
        messages.success(request, "Task details updated!")
        return redirect('item_detail', item_id=item.id)

    context = {
        'item': item,
        'comments': comments,
        'valid_assignees': valid_assignees,
        'priority_choices': BacklogItem.Priority.choices,
    }
    return render(request, 'taskStatus/item_detail.html', context)


@login_required
def update_item_status(request, item_id, new_status):
    item = get_object_or_404(BacklogItem, id=item_id)
    denied = _require_membership(request, item.project)
    if denied:
        return denied

    if request.method == 'POST':
        if not item.can_transition_to(new_status):
            messages.error(request, 'Invalid status transition.')
            return redirect('project_board', project_id=item.project_id)

        if new_status == 'SPRINT' and item.status == 'BACKLOG':
            active_sprint = item.project.active_sprint
            if not active_sprint:
                messages.error(request, 'No active sprint. Create and activate one first.')
                return redirect('project_board', project_id=item.project_id)
            item.sprint = active_sprint

        comment_body = request.POST.get('comment', '').strip()
        if comment_body:
            StageComment.objects.create(
                item=item,
                author_id=request.user.id,
                from_stage=item.status,
                to_stage=new_status,
                body=comment_body
            )

        item.status = new_status
        item.save()
        return redirect('project_board', project_id=item.project_id)

    context = {
        'item': item,
        'new_status': new_status,
        'new_status_display': dict(BacklogItem.Status.choices).get(new_status, new_status)
    }
    return render(request, 'taskStatus/transition_item.html', context)


@login_required
def update_item_priority(request, item_id, new_priority):
    item = get_object_or_404(BacklogItem, id=item_id)
    denied = _require_membership(request, item.project)
    if denied:
        return denied

    if request.method == 'POST':
        valid_priorities = [p[0] for p in BacklogItem.Priority.choices]
        if new_priority in valid_priorities:
            item.priority = new_priority
            item.save()
    return redirect('project_board', project_id=item.project_id)

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(BacklogItem, id=item_id)
    project_id = item.project.id
    denied = _require_membership(request, item.project)
    if denied:
        return denied

    if request.method == 'POST':
        item.delete()
        messages.success(request, "Task successfully deleted.")

    return redirect('project_board', project_id=project_id)

@login_required
def create_sprint(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    denied = _require_membership(request, project)
    if denied:
        return denied

    if request.method == 'POST':
        form = SprintForm(request.POST)
        if form.is_valid():
            sprint = form.save(commit=False)
            sprint.project = project
            sprint.save()
            messages.success(request, f'Sprint "{sprint.name}" created.')
    return redirect('project_board', project_id=project_id)


@login_required
def activate_sprint(request, sprint_id):
    sprint = get_object_or_404(Sprint, id=sprint_id)
    denied = _require_membership(request, sprint.project)
    if denied:
        return denied

    if request.method == 'POST':
        Sprint.objects.filter(
            project=sprint.project, status=Sprint.Status.ACTIVE
        ).update(status=Sprint.Status.CLOSED)

        sprint.status = Sprint.Status.ACTIVE
        sprint.save()
        messages.success(request, f'Sprint "{sprint.name}" is now active.')
    return redirect('project_board', project_id=sprint.project_id)


@login_required
def close_sprint(request, sprint_id):
    sprint = get_object_or_404(Sprint, id=sprint_id)
    denied = _require_membership(request, sprint.project)
    if denied:
        return denied

    if request.method == 'POST':
        sprint.status = Sprint.Status.CLOSED
        sprint.save()
        messages.success(request, f'Sprint "{sprint.name}" closed.')
    return redirect('project_board', project_id=sprint.project_id)

@login_required
def invite_collaborator(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.user.id != project.owner_id:
        messages.error(request, "Only the project owner can invite collaborators.")
        return redirect('project_board', project_id=project.id)

    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user_to_invite = User.objects.get(email=email)

            if user_to_invite.id not in project.collaborator_ids:
                project.collaborator_ids.append(user_to_invite.id)
                project.save()

            messages.success(request, f"Successfully added {user_to_invite.username} to the project!")

        except User.DoesNotExist:
            messages.error(request, "No user found with that email address.")

    return redirect('project_board', project_id=project.id)

@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.user.id != project.owner_id:
        messages.error(request, "Only the project owner can delete this project.")
        return redirect('project_board', project_id=project.id)

    if request.method == 'POST':
        project.delete()
        messages.success(request, "Project successfully deleted.")
        return redirect('project_list')

    return redirect('project_board', project_id=project.id)

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(StageComment, id=comment_id)
    denied = _require_membership(request, comment.item.project)
    if denied:
        return denied

    if request.user.id != comment.author_id:
        return HttpResponseForbidden("You can only edit your own comments.")

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            comment.body = body
            comment.save()
            messages.success(request, "Comment updated.")
        else:
            messages.error(request, "Comment cannot be empty.")

    return redirect('item_detail', item_id=comment.item_id)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(StageComment, id=comment_id)
    denied = _require_membership(request, comment.item.project)
    if denied:
        return denied

    if request.user.id != comment.author_id:
        return HttpResponseForbidden("You can only delete your own comments.")

    if request.method == 'POST':
        item_id = comment.item_id
        comment.delete()
        messages.success(request, "Comment deleted.")
        return redirect('item_detail', item_id=item_id)

    return redirect('item_detail', item_id=comment.item_id)
