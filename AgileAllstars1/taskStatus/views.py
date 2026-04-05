from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from sprints.models import Project, Sprint, BacklogItem
from .forms import ProjectForm, SprintForm, BacklogItemForm


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

    context = {
        'projects': Project.objects.all(),
        'form': form,
    }
    return render(request, 'taskStatus/project_list.html', context)


@login_required
def project_board(request, project_id):
    project = get_object_or_404(Project, id=project_id)
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
    if request.method == 'POST':
        form = BacklogItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.project = project
            item.created_by_id = request.user.id
            item.save()
            messages.success(request, f'"{item.title}" added to Product Backlog.')
    return redirect('project_board', project_id=project_id)


@login_required
def create_sprint(request, project_id):
    project = get_object_or_404(Project, id=project_id)
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
    if request.method == 'POST':
        sprint.status = Sprint.Status.CLOSED
        sprint.save()
        messages.success(request, f'Sprint "{sprint.name}" closed.')
    return redirect('project_board', project_id=sprint.project_id)


@login_required
def update_item_status(request, item_id, new_status):
    item = get_object_or_404(BacklogItem, id=item_id)
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

        item.status = new_status
        item.save()
    return redirect('project_board', project_id=item.project_id)


@login_required
def update_item_priority(request, item_id, new_priority):
    item = get_object_or_404(BacklogItem, id=item_id)
    if request.method == 'POST':
        valid_priorities = [p[0] for p in BacklogItem.Priority.choices]
        if new_priority in valid_priorities:
            item.priority = new_priority
            item.save()
    return redirect('project_board', project_id=item.project_id)
