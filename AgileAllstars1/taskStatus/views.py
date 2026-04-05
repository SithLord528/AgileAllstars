from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def index(request):
    return HttpResponse("Hello, world. You're at the task status page.")


MOCK_TASKS = [
    {"id": 1, "title": "Set up project structure", "description": "Initialize Django app.", "priority": "High", "story_points": 3, "status": "To Do", "assignee": "Alice"},
    {"id": 2, "title": "Design login page", "description": "Create login UI.", "priority": "High", "story_points": 5, "status": "In Progress", "assignee": "Bob"},
    {"id": 3, "title": "Write unit tests", "description": "Cover login flows.", "priority": "Medium", "story_points": 2, "status": "To Do", "assignee": "Unassigned"},
]


#@login_required
def backlog(request):
    """
    Display the product backlog.
 
    TODO (after models are created): Replace mock data with:
        tasks = Task.objects.filter(sprint__isnull=True).order_by('-priority', 'created_at')
        active_sprint = Sprint.objects.filter(status='active').first()
    """
    context = {
        "tasks": MOCK_TASKS,                   # swap with DB queryset later
        "active_sprint": None,                 # swap with active sprint query later
        "total_tasks": len(MOCK_TASKS),
        "priority_choices": ["High", "Medium", "Low"],
        "status_choices": ["To Do", "In Progress", "Done"],
    }
    return render(request, "backlog.html", context)
 
 
#@login_required
def add_task(request):
    """
    Handle new task creation via POST.
 
    TODO (after models are created): Replace with:
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
    """
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        priority = request.POST.get("priority", "Medium")
        story_points = request.POST.get("story_points", 0)
        assignee = request.POST.get("assignee", "Unassigned").strip()
 
        if not title:
            messages.error(request, "Task title is required.")
            return redirect("backlog")
 
        # ── DB save goes here ──────────────────────────────────
        # Task.objects.create(
        #     title=title,
        #     description=description,
        #     priority=priority,
        #     story_points=story_points,
        #     assignee=assignee,
        #     created_by=request.user,
        # )
        # ──────────────────────────────────────────────────────
 
        messages.success(request, f'Task "{title}" added to the backlog.')
    return redirect("backlog")
 
 
#@login_required
def start_sprint(request):
    """
    Handle sprint creation via POST.
 
    TODO (after models are created): Replace with:
        sprint = Sprint.objects.create(
            name=sprint_name,
            goal=sprint_goal,
            start_date=start_date,
            end_date=end_date,
            created_by=request.user,
        )
        # Move selected tasks into sprint:
        Task.objects.filter(id__in=task_ids).update(sprint=sprint)
    """
    if request.method == "POST":
        sprint_name = request.POST.get("sprint_name", "").strip()
        sprint_goal = request.POST.get("sprint_goal", "").strip()
        duration = request.POST.get("duration", "2")          # weeks
        task_ids = request.POST.getlist("task_ids")           # list of task PKs
 
        if not sprint_name:
            messages.error(request, "Sprint name is required.")
            return redirect("backlog")
 
        # ── DB save goes here ──────────────────────────────────
        # sprint = Sprint.objects.create(...)
        # Task.objects.filter(id__in=task_ids).update(sprint=sprint)
        # ──────────────────────────────────────────────────────
 
        messages.success(request, f'Sprint "{sprint_name}" started with {len(task_ids)} task(s).')
    return redirect("backlog")
 
 
#@login_required
def delete_task(request, task_id):
    """
    Handle task deletion.
 
    TODO (after models are created): Replace with:
        task = get_object_or_404(Task, id=task_id)
        task.delete()
    """
    if request.method == "POST":
        # Task.objects.filter(id=task_id).delete()
        messages.success(request, "Task deleted.")
    return redirect("backlog")
