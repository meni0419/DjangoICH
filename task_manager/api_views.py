from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import ExtractWeekDay

from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Task, Category, SubTask
from .serializers import (
    TaskSerializer,
    TaskCreateSerializer,
    SubTaskSerializer,
    SubTaskCreateSerializer,
)


class SubTaskPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class TaskViewSet(viewsets.ModelViewSet):
    """
    Полный CRUD для задач с фильтрацией, поиском, сортировкой.
    Дополнительно: фильтр по дню недели дедлайна (weekday=1..7, где 1=воскресенье).
    """
    queryset = Task.objects.all().prefetch_related('categories', 'subtasks')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # Фильтры по полям: статус и категории (по id)
    filterset_fields = {
        'status': ['exact'],
        'categories': ['exact'],
        'categories__id': ['exact'],
    }
    # Поиск по названию/описанию задачи и заголовкам подзадач
    search_fields = ['title', 'description', 'subtasks__title']
    # Сортировка по дате создания, дедлайну, статусу, названию
    ordering_fields = ['created_at', 'deadline', 'status', 'title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TaskCreateSerializer
        return TaskSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # Фильтр по дню недели дедлайна: weekday=1..7 (Sunday=1..Saturday=7)
        weekday_param = self.request.query_params.get('weekday')
        if weekday_param is not None:
            try:
                day_number = int(weekday_param)
            except (TypeError, ValueError):
                day_number = None
            if day_number in range(1, 8):
                qs = qs.annotate(deadline_weekday=ExtractWeekDay('deadline')).filter(
                    deadline_weekday=day_number
                )
        return qs

    @action(detail=True, methods=['get'], url_path='subtasks')
    def subtasks(self, request, pk=None):
        """
        Кастомный маршрут: /tasks/{id}/subtasks/ — подзадачи конкретной задачи.
        Поддерживает фильтр по статусу и пагинацию (5 на страницу).
        """
        task = get_object_or_404(Task, pk=pk)
        subtasks_qs = task.subtasks.all().order_by('-created_at')

        status_filter = request.query_params.get('status')
        if status_filter:
            subtasks_qs = subtasks_qs.filter(status=status_filter)

        paginator = SubTaskPagination()
        page = paginator.paginate_queryset(subtasks_qs, request, view=self)
        serializer = SubTaskSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SubTaskViewSet(viewsets.ModelViewSet):
    """
    Полный CRUD для подзадач с фильтрацией, поиском, сортировкой.
    Пагинация: 5 на страницу.
    """
    queryset = SubTask.objects.select_related('task').all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # Фильтрация: по статусу, по задаче (id), по статусу задачи при необходимости
    filterset_fields = {
        'status': ['exact'],
        'task': ['exact'],
        'task__status': ['exact'],
    }
    # Поиск по названию/описанию подзадачи и названию задачи
    search_fields = ['title', 'description', 'task__title']
    # Сортировка по датам, статусу, названию
    ordering_fields = ['created_at', 'deadline', 'status', 'title', 'task__title']
    ordering = ['-created_at']
    pagination_class = SubTaskPagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SubTaskCreateSerializer
        return SubTaskSerializer


@api_view(['GET'])
def task_analytics_api_view(request):
    """Оставлено без изменений"""
    now = timezone.now()
    total_tasks = Task.objects.count()

    status_counts = Task.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    status_stats = {item['status']: item['count'] for item in status_counts}

    all_statuses = ['NEW', 'IN_PROGRESS', 'PENDING', 'BLOCKED', 'DONE']
    for status_choice in all_statuses:
        if status_choice not in status_stats:
            status_stats[status_choice] = 0

    overdue_tasks = Task.objects.filter(
        deadline__lt=now,
        status__in=['NEW', 'IN_PROGRESS', 'PENDING', 'BLOCKED']
    ).count()

    completed_tasks = status_stats.get('DONE', 0)
    in_progress_tasks = status_stats.get('IN_PROGRESS', 0)

    next_week = now + timezone.timedelta(days=7)
    upcoming_tasks = Task.objects.filter(
        deadline__gte=now,
        deadline__lte=next_week,
        status__in=['NEW', 'IN_PROGRESS', 'PENDING', 'BLOCKED']
    ).count()

    category_stats = Category.objects.annotate(
        task_count=Count('task')
    ).values('name', 'task_count').order_by('-task_count')

    analytics_data = {
        'summary': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'overdue_tasks': overdue_tasks,
            'upcoming_tasks': upcoming_tasks,
        },
        'status_breakdown': status_stats,
        'category_breakdown': list(category_stats),
        'time_analysis': {
            'overdue_count': overdue_tasks,
            'upcoming_due_count': upcoming_tasks,
            'completion_rate': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2)
        }
    }

    return Response(analytics_data)


@api_view(['GET'])
def task_analytics_api_view(request):
    """API endpoint for task analytics and statistics"""

    # Get current time for overdue calculation
    now = timezone.now()

    # Total tasks count
    total_tasks = Task.objects.count()

    # Count tasks by status
    status_counts = Task.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    # Convert to dictionary for easier handling
    status_stats = {item['status']: item['count'] for item in status_counts}

    # Ensure all statuses are represented
    all_statuses = ['NEW', 'IN_PROGRESS', 'PENDING', 'BLOCKED', 'DONE']
    for status_choice in all_statuses:
        if status_choice not in status_stats:
            status_stats[status_choice] = 0

    # Count overdue tasks (deadline passed and not completed)
    overdue_tasks = Task.objects.filter(
        deadline__lt=now,
        status__in=['NEW', 'IN_PROGRESS', 'PENDING', 'BLOCKED']
    ).count()

    # Additional analytics
    completed_tasks = status_stats.get('DONE', 0)
    in_progress_tasks = status_stats.get('IN_PROGRESS', 0)

    # Tasks due in next 7 days
    next_week = now + timezone.timedelta(days=7)
    upcoming_tasks = Task.objects.filter(
        deadline__gte=now,
        deadline__lte=next_week,
        status__in=['NEW', 'IN_PROGRESS', 'PENDING', 'BLOCKED']
    ).count()

    # Category statistics
    category_stats = Category.objects.annotate(
        task_count=Count('task')
    ).values('name', 'task_count').order_by('-task_count')

    analytics_data = {
        'summary': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'overdue_tasks': overdue_tasks,
            'upcoming_tasks': upcoming_tasks,
        },
        'status_breakdown': status_stats,
        'category_breakdown': list(category_stats),
        'time_analysis': {
            'overdue_count': overdue_tasks,
            'upcoming_due_count': upcoming_tasks,
            'completion_rate': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2)
        }
    }

    return Response(analytics_data)
