from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.models import User

from sprints.models import Project, Sprint, BacklogItem, StageComment
from sprints.forms import ProjectForm, SprintForm, BacklogItemForm

@login_required
def project_list(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner_id = request.user.id
            try:
                project.save()
                messages.success(request, "Project created successfully!")
            except IntegrityError:
                messages.error(request, "A project with this name already exists!")
            return redirect('project_list')
    else:
        form = ProjectForm()

    owned_projects = list(Project.objects.filter(owner_id=request.user.id))
    
    all_other_projects = Project.objects.exclude(owner_id=request.user.id)
    shared_projects = [
        p for p in all_other_projects 
        if p.collaborator_ids and request.user.id in p.collaborator_ids
    ]
    
    projects = owned_projects + shared_projects

    return render(request, 'taskStatus/project_list.html', {'projects': projects, 'form': form})

@login_required
def project_board(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.user.id != project.owner_id and (not project.collaborator_ids or request.user.id not in project.collaborator_ids):
        messages.error(request, "You do not have access to this project.")
        return redirect('project_list')

    active_sprint = project.sprints.filter(status='ACTIVE').first()
    planning_sprints = project.sprints.exclude(status='ACTIVE').exclude(status='CLOSED')
    
    backlog_items = project.backlog_items.filter(status='BACKLOG')
    sprint_items = project.backlog_items.filter(status='SPRINT')
    test_items = project.backlog_items.filter(status='TEST')
    complete_items = project.backlog_items.filter(status='DONE')

    total_items = project.backlog_items.count()
    completion = int((complete_items.count() / total_items) * 100) if total_items > 0 else 0
    
    sprint_completion = 0
    if active_sprint:
        active_total = project.backlog_items.filter(status__in=['SPRINT', 'TEST', 'DONE']).count()
        active_done = complete_items.count()
        sprint_completion = int((active_done / active_total) * 100) if active_total > 0 else 0

    context = {
        'project': project,
        'active_sprint': active_sprint,
        'planning_sprints': planning_sprints,
        'backlog_items': backlog_items,
        'sprint_items': sprint_items,
        'test_items': test_items,
        'complete_items': complete_items,
        'completion': completion,
        'sprint_completion': sprint_completion,
        'item_form': BacklogItemForm(),
        'sprint_form': SprintForm(),
    }
    return render(request, 'taskStatus/taskBoard.html', context)

@login_required
def create_sprint(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = SprintForm(request.POST)
        if form.is_valid():
            sprint = form.save(commit=False)
            sprint.project = project
            try:
                sprint.save()
                messages.success(request, "Sprint created!")
            except IntegrityError:
                messages.error(request, "A sprint with this name already exists in this project!")
    return redirect('project_board', project_id=project.id)

@login_required
def activate_sprint(request, sprint_id):
    sprint = get_object_or_404(Sprint, id=sprint_id)
    project = sprint.project
    
    active = project.sprints.filter(status='ACTIVE').first()
    if active:
        active.status = 'CLOSED'
        active.save()
        
    sprint.status = 'ACTIVE'
    sprint.save()
    messages.success(request, f"Sprint '{sprint.name}' is now active!")
    return redirect('project_board', project_id=project.id)

@login_required
def close_sprint(request, sprint_id):
    sprint = get_object_or_404(Sprint, id=sprint_id)
    project = sprint.project  # FIXED: Define project before using it
    sprint.status = 'CLOSED'
    sprint.save()
    messages.success(request, f"Sprint '{sprint.name}' closed.")
    return redirect('project_board', project_id=project.id)

@login_required
def edit_sprint(request, sprint_id):
    sprint = get_object_or_404(Sprint, id=sprint_id)
    if request.method == 'POST':
        # Updating fields directly from POST data
        sprint.name = request.POST.get('name', sprint.name)
        sprint.goal = request.POST.get('goal', sprint.goal)
        
        # Adding support for dates if they are in your form
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if start_date: sprint.start_date = start_date
        if end_date: sprint.end_date = end_date
        
        try:
            sprint.save()
            messages.success(request, "Sprint updated!")
        except IntegrityError:
            messages.error(request, "A sprint with this name already exists in this project!")
        return redirect('project_board', project_id=sprint.project.id)

@login_required
def create_item(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = BacklogItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.project = project
            item.created_by_id = request.user.id  # FIXED: Assign to _id
            try:
                item.save()
                messages.success(request, "Task added to backlog!")
            except IntegrityError:
                messages.error(request, "A task with this title already exists in this project!")
    return redirect('project_board', project_id=project.id)

@login_required
def invite_collaborator(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user_to_invite = User.objects.get(email=email)
            if user_to_invite.id == project.owner_id:
                messages.error(request, "You are already the owner of this project.")
            elif project.collaborator_ids and user_to_invite.id in project.collaborator_ids:
                messages.info(request, "This user is already a collaborator.")
            else:
                if not project.collaborator_ids:
                    project.collaborator_ids = []
                project.collaborator_ids.append(user_to_invite.id)
                project.save()
                messages.success(request, f"Successfully invited {user_to_invite.username}!")
        except User.DoesNotExist:
            messages.error(request, "No user found with that email address.")
    return redirect('project_board', project_id=project.id)

@login_required
def item_detail(request, item_id):
    item = get_object_or_404(BacklogItem, id=item_id)
    project = item.project
    comments = item.transition_comments.all()

    collab_ids = project.collaborator_ids or []
    valid_assignees = list(User.objects.filter(id__in=collab_ids))
    try:
        project_owner = User.objects.get(id=project.owner_id)
        if project_owner not in valid_assignees:
            valid_assignees.insert(0, project_owner)
    except User.DoesNotExist:
        pass

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_comment':
            body = request.POST.get('comment_body')
            if body:
                StageComment.objects.create(
                    item=item,
                    author_id=request.user.id, 
                    body=body,
                    from_stage=item.status,
                    to_stage=item.status
                )
                messages.success(request, "Comment added.")
                
        elif action == 'update_details':
            item.title = request.POST.get('title', item.title)
            item.description = request.POST.get('description', item.description)
            
            assignee_id = request.POST.get('assignee')
            if assignee_id:
                item.assigned_to_id = int(assignee_id)
            else:
                item.assigned_to_id = None 
                
            new_priority = request.POST.get('priority')
            valid_priorities = [p[0] for p in BacklogItem.Priority.choices]
            if new_priority in valid_priorities:
                item.priority = new_priority

            try:
                item.save()
                messages.success(request, "Task details updated!")
            except IntegrityError:
                messages.error(request, "A task with this title already exists in this project!")

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
    
    valid_statuses = [choice[0] for choice in BacklogItem.Status.choices]
    if new_status not in valid_statuses:
        return redirect('project_board', project_id=item.project.id)

    if request.method == 'POST':
        comment_body = request.POST.get('comment', '').strip()
        old_status = item.status
        item.status = new_status
        item.save()
        
        if comment_body:
            StageComment.objects.create(
                item=item,
                author_id=request.user.id, 
                from_stage=old_status,
                to_stage=new_status,
                body=comment_body
            )
        messages.success(request, f"Task moved to {item.get_status_display()}")
        return redirect('project_board', project_id=item.project.id)
        
    context = {
        'item': item,
        'new_status_code': new_status,
        'new_status_display': dict(BacklogItem.Status.choices).get(new_status, new_status),
    }
    return render(request, 'taskStatus/transition_item.html', context)

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
def delete_item(request, item_id):
    item = get_object_or_404(BacklogItem, id=item_id)
    project_id = item.project.id
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Task successfully deleted.")
    return redirect('project_board', project_id=project_id)

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(StageComment, id=comment_id)
    item_id = comment.item.id
    if request.method == 'POST' and comment.author_id == request.user.id:
        comment.delete()
        messages.success(request, "Comment deleted.")
    return redirect('item_detail', item_id=item_id)

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(StageComment, id=comment_id)
    if comment.author_id != request.user.id:
        messages.error(request, "You can only edit your own comments.")
        return redirect('item_detail', item_id=comment.item.id)
        
    if request.method == 'POST':
        comment.body = request.POST.get('body', comment.body)
        comment.save()
        messages.success(request, "Comment updated.")
        return redirect('item_detail', item_id=comment.item.id)
        
    return render(request, 'taskStatus/edit_comment.html', {'comment': comment})