from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import (
    TaskListCreateAPIView,
    TaskRetrieveUpdateDestroyAPIView,
    SubTaskListCreateAPIView,
    SubTaskRetrieveUpdateDestroyAPIView,
    task_analytics_api_view, CategoryViewSet, MyTasksListAPIView,
)

app_name = 'task_manager_api'
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category'
                )

urlpatterns = [
    # category
    path('', include(router.urls)),

    # Tasks
    path('tasks/', TaskListCreateAPIView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskRetrieveUpdateDestroyAPIView.as_view(), name='task-detail'),
    path('tasks/my/', MyTasksListAPIView.as_view(), name='my-tasks'),

    # SubTasks
    path('subtasks/', SubTaskListCreateAPIView.as_view(), name='subtask-list-create'),
    path('subtasks/<int:pk>/', SubTaskRetrieveUpdateDestroyAPIView.as_view(), name='subtask-detail'),

    # Analytics (оставляем как есть)
    path('tasks/analytics/', task_analytics_api_view, name='task-analytics'),
]
