from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count
from .models import Task, Category, SubTask
from .serializers import TaskSerializer, TaskCreateSerializer, SubTaskSerializer, SubTaskCreateSerializer


class TaskCreateAPIView(generics.CreateAPIView):
    """API endpoint for creating tasks"""
    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        # Return full task data using TaskSerializer
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class TaskListAPIView(generics.ListAPIView):
    """API endpoint for getting list of tasks"""
    queryset = Task.objects.all().prefetch_related('categories', 'subtasks')
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by category
        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(categories__id=category_filter)

        return queryset


class TaskDetailAPIView(generics.RetrieveAPIView):
    """API endpoint for getting a specific task by ID"""
    queryset = Task.objects.all().prefetch_related('categories', 'subtasks')
    serializer_class = TaskSerializer


class SubTaskListCreateView(APIView):
    """API endpoint for creating subtasks"""

    def get(self, request):
        """Get list of all subtasks"""
        task_id = request.GET.get('task_id')

        if task_id:
            subtasks = SubTask.objects.filter(task_id=task_id)
        else:
            subtasks = SubTask.objects.all()

        status_filter = request.query_params.get('status')
        if status_filter:
            subtasks = subtasks.filter(status=status_filter)

        subtasks = subtasks.select_related('task').order_by('-created_at')
        serializer = SubTaskSerializer(subtasks, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new subtask"""
        serializer = SubTaskCreateSerializer(data=request.data)
        if serializer.is_valid():
            subtask = serializer.save()
            # Return full subtask data
            response_serializer = SubTaskSerializer(subtask)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubTaskDetailUpdateDeleteView(APIView):
    """API endpoint for updating and deleting a specific subtask by ID"""

    def get_object(self, pk):
        """Helper method to get subtask object"""
        return get_object_or_404(SubTask, pk=pk)

    def get(self, request, pk):
        """Get subtask details"""
        subtask = self.get_object(pk)
        serializer = SubTaskSerializer(subtask)
        return Response(serializer.data)

    def put(self, request, pk):
        """Update subtask details"""
        subtask = self.get_object(pk)
        serializer = SubTaskCreateSerializer(subtask, data=request.data)
        if serializer.is_valid():
            updated_subtask = serializer.save()
            # Return full subtask data
            response_serializer = SubTaskSerializer(updated_subtask)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Partially update subtask details"""
        subtask = self.get_object(pk)
        serializer = SubTaskCreateSerializer(subtask, data=request.data, partial=True)
        if serializer.is_valid():
            updated_subtask = serializer.save()
            response_serializer = SubTaskSerializer(updated_subtask)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete specific subtask"""
        subtask = self.get_object(pk)
        subtask_title = subtask.title
        subtask.delete()
        return Response(
            {'message': f'SubTask "{subtask_title}" has been deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


class TaskSubTasksView(APIView):
    """
    API view for getting all subtasks of a specific task
    """

    def get(self, request, task_id):
        """Get all subtasks for a specific task"""
        task = get_object_or_404(Task, pk=task_id)
        subtasks = task.subtasks.all().order_by('-created_at')

        # Optional: filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            subtasks = subtasks.filter(status=status_filter)

        serializer = SubTaskSerializer(subtasks, many=True)
        return Response({
            'task_id': task.id,
            'task_title': task.title,
            'subtasks_count': subtasks.count(),
            'subtasks': serializer.data
        })


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
