from django.urls import path
from . import views
from .admin import task_admin_site

app_name = 'task_manager'

urlpatterns = [
    path('', views.index, name='index'),  # /tasks/ - for the index view
    path('list/', views.tasks, name='tasks'),  # /tasks/list/ - for the tasks list
    path('<int:task_id>/', views.task_detail, name='task_detail'),  # /tasks/1/
    path('admin/', task_admin_site.urls),  # /tasks/admin/
]


