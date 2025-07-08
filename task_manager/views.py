from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from .models import Task, SubTask, Category


def index(request):
    # Show a simple dashboard or redirect to tasks
    return redirect('task_manager:tasks')


def tasks(request):
    tasks = Task.objects.all().order_by('-created_at')
    categories = Category.objects.all()

    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    # Filter by category if provided
    category_filter = request.GET.get('category')
    if category_filter:
        tasks = tasks.filter(categories__id=category_filter)

    context = {
        'tasks': tasks,
        'categories': categories,
        'status_choices': Task._meta.get_field('status').choices,
        'current_status': status_filter,
        'current_category': int(category_filter) if category_filter else None,
    }
    return render(request, 'task_manager/tasks.html', context)


def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    subtasks = task.subtasks.all().order_by('-created_at')

    # Calculate deadline status
    now = timezone.now()
    deadline_status = 'safe'

    if task.deadline <= now + timedelta(days=1):
        deadline_status = 'warning'  # Due within 1 day
    elif task.deadline <= now + timedelta(days=7):
        deadline_status = 'upcoming'  # Due within 7 days

    context = {
        'task': task,
        'subtasks': subtasks,
        'deadline_status': deadline_status,
    }
    return render(request, 'task_manager/task_detail.html', context)