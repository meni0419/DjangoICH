from rest_framework import generics, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count

from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny

from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet

from .models import Task, Category, SubTask
from .serializers import (
    TaskSerializer,
    TaskCreateSerializer,
    SubTaskSerializer,
    SubTaskCreateSerializer, CategoryCreateSerializer, CategorySerializer,
)


class CategoryCursorPagination(CursorPagination):
    page_size = 5
    ordering = 'name'
    page_size_query_param = None


class CategoryViewSet(ModelViewSet):
    """
    Полный CRUD для категорий.
    - Мягкое удаление в destroy()
    - Экшен count_tasks: агрегированный подсчёт задач по всем категориям
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Category.objects.all().order_by('name')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    pagination_class = CategoryCursorPagination

    def get_serializer_class(self):
        # Для создания/обновления используем валидирующий сериализатор
        if self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateSerializer
        return CategorySerializer

    def destroy(self, request, *args, **kwargs):
        # Мягкое удаление: вызываем переопределённый delete() модели
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='count_tasks')
    def count_tasks(self, request, *args, **kwargs):
        """
        Возвращает список категорий с количеством связанных задач.
        Только активные (не «удалённые») категории.
        """
        data = (
            Category.objects
            .annotate(task_count=Count('task'))  # обратная связь M2M по Task.categories
            .values('id', 'name', 'task_count')
            .order_by('name')
        )
        return Response(list(data), status=status.HTTP_200_OK)


class SubTaskPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


# ========== Tasks ==========
class TaskListCreateAPIView(generics.ListCreateAPIView):
    """
    List + Create tasks.
    Фильтрация: status, deadline (__gte/__lte).
    Поиск: title, description.
    Сортировка: created_at (по умолчанию -created_at).
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Task.objects.all().prefetch_related('categories', 'subtasks').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'status': ['exact'],
        'deadline': ['exact', 'gte', 'lte'],
    }
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        # Для GET отдаём подробный TaskSerializer, для POST используем TaskCreateSerializer
        if self.request and self.request.method == 'POST':
            return TaskCreateSerializer
        return TaskSerializer

    def create(self, request, *args, **kwargs):
        # Переопределяем для того, чтобы после создания вернуть полные данные TaskSerializer
        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class TaskRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve + Update + Destroy task.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Task.objects.all().prefetch_related('categories', 'subtasks')
    lookup_field = 'pk'

    def get_serializer_class(self):
        # Для чтения — полный TaskSerializer; для обновления — TaskCreateSerializer
        if self.request and self.request.method in ['PUT', 'PATCH']:
            return TaskCreateSerializer
        return TaskSerializer


# ========== SubTasks ==========
class SubTaskListCreateAPIView(generics.ListCreateAPIView):
    """
    List + Create subtasks.
    Фильтрация: status, deadline (__gte/__lte).
    Поиск: title, description.
    Сортировка: created_at (по умолчанию -created_at).
    Пагинация: 5 на страницу.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = SubTask.objects.select_related('task').all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'status': ['exact'],
        'deadline': ['exact', 'gte', 'lte'],
    }
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    pagination_class = SubTaskPagination

    def get_serializer_class(self):
        if self.request and self.request.method == 'POST':
            return SubTaskCreateSerializer
        return SubTaskSerializer


class SubTaskRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve + Update + Destroy subtask.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = SubTask.objects.select_related('task').all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request and self.request.method in ['PUT', 'PATCH']:
            return SubTaskCreateSerializer
        return SubTaskSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
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
