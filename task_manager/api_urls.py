from django.urls import path
from .api_views import (
    TaskCreateAPIView,
    TaskListAPIView,
    TaskDetailAPIView,
    task_analytics_api_view
)

app_name = 'task_manager_api'

urlpatterns = [
    # Task endpoints
    path('tasks/', TaskListAPIView.as_view(), name='task-list'),
    path('tasks/create/', TaskCreateAPIView.as_view(), name='task-create'),
    path('tasks/<int:pk>/', TaskDetailAPIView.as_view(), name='task-detail'),

    # Analytics endpoint
    path('tasks/analytics/', task_analytics_api_view, name='task-analytics'),
]