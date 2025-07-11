from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta, datetime
from django.db.models import Q
from .models import Task, SubTask, Category
from .forms import TaskForm, SubTaskForm, CategoryForm


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

    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    date_field = request.GET.get('date_field', 'created_at')  # Default to created_at

    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            if date_field == 'deadline':
                tasks = tasks.filter(deadline__date__gte=date_from_parsed)
            else:  # created_at
                tasks = tasks.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass  # Invalid date format, ignore filter

    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            if date_field == 'deadline':
                tasks = tasks.filter(deadline__date__lte=date_to_parsed)
            else:  # created_at
                tasks = tasks.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass  # Invalid date format, ignore filter

    context = {
        'tasks': tasks,
        'categories': categories,
        'status_choices': Task._meta.get_field('status').choices,
        'current_status': status_filter,
        'current_category': int(category_filter) if category_filter else None,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'current_date_field': date_field,
    }
    return render(request, 'task_manager/tasks.html', context)


def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    all_subtasks = task.subtasks.all()

    # Filter subtasks by status if provided
    subtask_status_filter = request.GET.get('subtask_status')
    if subtask_status_filter:
        all_subtasks = all_subtasks.filter(status=subtask_status_filter)

    # Filter subtasks by date range
    subtask_date_from = request.GET.get('subtask_date_from')
    subtask_date_to = request.GET.get('subtask_date_to')
    subtask_date_field = request.GET.get('subtask_date_field', 'created_at')  # Default to created_at

    if subtask_date_from:
        try:
            date_from_parsed = datetime.strptime(subtask_date_from, '%Y-%m-%d').date()
            if subtask_date_field == 'deadline':
                all_subtasks = all_subtasks.filter(deadline__date__gte=date_from_parsed)
            else:  # created_at
                all_subtasks = all_subtasks.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass  # Invalid date format, ignore filter

    if subtask_date_to:
        try:
            date_to_parsed = datetime.strptime(subtask_date_to, '%Y-%m-%d').date()
            if subtask_date_field == 'deadline':
                all_subtasks = all_subtasks.filter(deadline__date__lte=date_to_parsed)
            else:  # created_at
                all_subtasks = all_subtasks.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass  # Invalid date format, ignore filter

    subtasks = all_subtasks.order_by('-created_at')

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
        'all_subtasks': task.subtasks.all(),  # For statistics (unfiltered)
        'deadline_status': deadline_status,
        'status_choices': SubTask._meta.get_field('status').choices,
        'current_subtask_status': subtask_status_filter,
        'current_subtask_date_from': subtask_date_from,
        'current_subtask_date_to': subtask_date_to,
        'current_subtask_date_field': subtask_date_field,
    }
    return render(request, 'task_manager/task_detail.html', context)


def categories(request):
    categories = Category.objects.all().order_by('name')
    context = {
        'categories': categories,
    }
    return render(request, 'task_manager/categories.html', context)


# CREATE VIEWS
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('task_manager:categories')
    else:
        form = CategoryForm()

    context = {
        'form': form,
        'title': 'Create New Category'
    }
    return render(request, 'task_manager/create_category.html', context)


def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('task_manager:task_detail', task_id=task.id)
    else:
        form = TaskForm()

    context = {
        'form': form,
        'title': 'Create New Task'
    }
    return render(request, 'task_manager/create_task.html', context)


def create_subtask(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        form = SubTaskForm(request.POST)
        if form.is_valid():
            subtask = form.save(commit=False)
            subtask.task = task
            subtask.save()
            messages.success(request, f'Subtask "{subtask.title}" created successfully!')
            return redirect('task_manager:task_detail', task_id=task.id)
    else:
        form = SubTaskForm()

    context = {
        'form': form,
        'task': task,
        'title': f'Create Subtask for "{task.title}"'
    }
    return render(request, 'task_manager/create_subtask.html', context)


# EDIT VIEWS
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('task_manager:categories')
    else:
        form = CategoryForm(instance=category)

    context = {
        'form': form,
        'title': f'Edit Category: {category.name}',
        'category': category
    }
    return render(request, 'task_manager/edit_category.html', context)


def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('task_manager:task_detail', task_id=task.id)
    else:
        form = TaskForm(instance=task)

    context = {
        'form': form,
        'title': f'Edit Task: {task.title}',
        'task': task
    }
    return render(request, 'task_manager/edit_task.html', context)


def edit_subtask(request, subtask_id):
    subtask = get_object_or_404(SubTask, id=subtask_id)

    if request.method == 'POST':
        form = SubTaskForm(request.POST, instance=subtask)
        if form.is_valid():
            subtask = form.save()
            messages.success(request, f'Subtask "{subtask.title}" updated successfully!')
            return redirect('task_manager:task_detail', task_id=subtask.task.id)
    else:
        form = SubTaskForm(instance=subtask)

    context = {
        'form': form,
        'title': f'Edit Subtask: {subtask.title}',
        'subtask': subtask,
        'task': subtask.task
    }
    return render(request, 'task_manager/edit_subtask.html', context)


# DELETE VIEWS
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        category_name = category.name
        tasks_count = category.task_set.count()
        category.delete()
        messages.success(request, f'Category "{category_name}" and {tasks_count} related tasks deleted successfully!')
        return redirect('task_manager:categories')

    context = {
        'category': category,
        'tasks_count': category.task_set.count()
    }
    return render(request, 'task_manager/delete_category.html', context)


def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        task_title = task.title
        subtasks_count = task.subtasks.count()
        task.delete()  # This will automatically delete all subtasks due to CASCADE
        messages.success(request, f'Task "{task_title}" and {subtasks_count} subtasks deleted successfully!')
        return redirect('task_manager:tasks')

    context = {
        'task': task,
        'subtasks_count': task.subtasks.count()
    }
    return render(request, 'task_manager/delete_task.html', context)


def delete_subtask(request, subtask_id):
    subtask = get_object_or_404(SubTask, id=subtask_id)

    if request.method == 'POST':
        subtask_title = subtask.title
        task_id = subtask.task.id
        subtask.delete()
        messages.success(request, f'Subtask "{subtask_title}" deleted successfully!')
        return redirect('task_manager:task_detail', task_id=task_id)

    context = {
        'subtask': subtask,
        'task': subtask.task
    }
    return render(request, 'task_manager/delete_subtask.html', context)