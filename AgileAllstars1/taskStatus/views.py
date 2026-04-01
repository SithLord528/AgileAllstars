from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Task
from .forms import TaskForm

def index(request):
    return HttpResponse('<h1>Task Status Page</h1>')

@login_required 
def task_board(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            new_task = form.save(commit=False)
            new_task.user = request.user 
            new_task.save()
            
            return redirect('task_board') 
    else:
        form = TaskForm()

    user_tasks = Task.objects.filter(user=request.user)

    context = {
        'todo_tasks': user_tasks.filter(status=Task.Status.TODO),
        'in_progress_tasks': user_tasks.filter(status=Task.Status.IN_PROGRESS),
        'testing_tasks': user_tasks.filter(status=Task.Status.TESTING),
        'completed_tasks': user_tasks.filter(status=Task.Status.COMPLETED),
        'form': form, 
    }

    return render(request, 'taskStatus/taskBoard.html', context)

@login_required
def update_task_status(request, task_id, new_status):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    valid_statuses = [status[0] for status in Task.Status.choices]
    if new_status in valid_statuses:
        task.status = new_status
        task.save()
        
    return redirect('task_board')