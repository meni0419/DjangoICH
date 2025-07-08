
from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import Task, SubTask, Category

# Create custom admin site for task_manager
class TaskManagerAdminSite(AdminSite):
    site_header = 'Task Manager Administration'
    site_title = 'Task Manager Admin'
    index_title = 'Welcome to Task Manager Administration'

# Create instance of custom admin site
task_admin_site = TaskManagerAdminSite(name='task_admin')

# Register models with custom admin site
@admin.register(Task, site=task_admin_site)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'deadline', 'created_at']
    list_filter = ['status', 'created_at', 'deadline']
    search_fields = ['title', 'description']
    filter_horizontal = ['categories']

@admin.register(SubTask, site=task_admin_site)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task', 'status', 'deadline', 'created_at']
    list_filter = ['status', 'created_at', 'deadline']
    search_fields = ['title', 'description']

@admin.register(Category, site=task_admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

# Also register with default admin (optional)
admin.site.register(Task, TaskAdmin)
admin.site.register(SubTask, SubTaskAdmin)
admin.site.register(Category, CategoryAdmin)