from django.urls import path
from . import views
from .admin import task_admin_site

app_name = 'task_manager'

urlpatterns = [
    path('', views.index, name='index'),  # /tasks/ - for the index view
    path('list/', views.tasks, name='tasks'),  # /tasks/list/ - for the tasks list
    path('<int:task_id>/', views.task_detail, name='task_detail'),  # /tasks/1/

    # Create pages
    path('create/category/', views.create_category, name='create_category'),  # /tasks/create/category/
    path('create/task/', views.create_task, name='create_task'),  # /tasks/create/task/
    path('create/subtask/<int:task_id>/', views.create_subtask, name='create_subtask'),  # /tasks/create/subtask/1/

    # Edit pages
    path('edit/category/<int:category_id>/', views.edit_category, name='edit_category'),  # /tasks/edit/category/1/
    path('edit/task/<int:task_id>/', views.edit_task, name='edit_task'),  # /tasks/edit/task/1/
    path('edit/subtask/<int:subtask_id>/', views.edit_subtask, name='edit_subtask'),  # /tasks/edit/subtask/1/

    # Delete pages
    path('delete/category/<int:category_id>/', views.delete_category, name='delete_category'),
    # /tasks/delete/category/1/
    path('delete/task/<int:task_id>/', views.delete_task, name='delete_task'),  # /tasks/delete/task/1/
    path('delete/subtask/<int:subtask_id>/', views.delete_subtask, name='delete_subtask'),  # /tasks/delete/subtask/1/

    # Categories list
    path('categories/', views.categories, name='categories'),  # /tasks/categories/

    path('admin/', task_admin_site.urls),  # /tasks/admin/
]
