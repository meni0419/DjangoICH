from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import (
    TaskViewSet,
    SubTaskViewSet,
    task_analytics_api_view,
)

app_name = 'task_manager_api'

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'subtasks', SubTaskViewSet, basename='subtask')

urlpatterns = [
    path('', include(router.urls)),
    path('tasks/analytics/', task_analytics_api_view, name='task-analytics'),
]