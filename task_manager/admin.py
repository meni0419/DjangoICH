from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Task, SubTask, Category


def create_short_title_method(field_name, max_length=10):
    """
    Универсальная функция для создания методов сокращения названий.

    Args:
        field_name: имя поля для сокращения (например, 'title' или 'task.title')
        max_length: максимальная длина отображаемого текста

    Returns:
        Метод для использования в админ классах
    """

    def short_title_method(self, obj):
        # Получаем значение поля через getattr с поддержкой вложенных полей
        field_parts = field_name.split('.')
        value = obj
        for part in field_parts:
            value = getattr(value, part)

        if len(value) > max_length:
            return format_html(
                '<span title="{}">{}</span>',
                value,  # Полное название в tooltip
                value[:max_length] + '...'  # Укороченное название
            )
        return value

    # Настраиваем атрибуты метода (вычисляем field_parts здесь)
    field_parts = field_name.split('.')
    short_title_method.short_description = field_parts[-1].title()
    short_title_method.admin_order_field = field_name

    return short_title_method


# Create custom admin site for task_manager
class TaskManagerAdminSite(AdminSite):
    site_header = 'Task Manager Administration'
    site_title = 'Task Manager Admin'
    index_title = 'Welcome to Task Manager Administration'


# Create instance of custom admin site
task_admin_site = TaskManagerAdminSite(name='task_admin')


# Inline class for SubTask
class SubTaskInline(admin.TabularInline):
    model = SubTask
    extra = 1  # Количество пустых форм для создания новых подзадач
    fields = ['title', 'description', 'status', 'deadline']


# Register models with custom admin site
@admin.register(Task, site=task_admin_site)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['short_title', 'status', 'deadline', 'created_at']
    list_filter = ['status', 'created_at', 'deadline']
    search_fields = ['title', 'description']
    filter_horizontal = ['categories']
    inlines = [SubTaskInline]  # Добавляем инлайн форму для подзадач

    # Используем универсальную функцию для создания метода сокращения
    short_title = create_short_title_method('title')


@admin.register(SubTask, site=task_admin_site)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ['short_title', 'task_short_title', 'status', 'deadline', 'created_at']
    list_filter = ['status', 'created_at', 'deadline']
    search_fields = ['title', 'description']
    actions = ['mark_as_done', 'show_done_subtasks']  # Добавляем оба custom action

    # Используем универсальную функцию для создания методов сокращения
    short_title = create_short_title_method('title')
    task_short_title = create_short_title_method('task.title')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Настраивает отображение полных названий в формах выбора"""
        if db_field.name == "task":
            # В формах выбора показываем полное название
            kwargs["queryset"] = Task.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def mark_as_done(self, request, queryset):
        """Custom action для перевода выбранных подзадач в статус Done"""
        # Получаем только те подзадачи, которые еще не в статусе Done
        subtasks_to_update = queryset.exclude(status='DONE')

        if not subtasks_to_update.exists():
            self.message_user(
                request,
                "Все выбранные подзадачи уже имеют статус 'Done'.",
                level=messages.WARNING
            )
            return

        # Обновляем статус подзадач
        updated_count = subtasks_to_update.update(status='DONE')

        # Показываем сообщение о результате
        if updated_count == 1:
            message = "1 подзадача успешно переведена в статус 'Done'."
        else:
            message = f"{updated_count} подзадач успешно переведены в статус 'Done'."

        self.message_user(request, message, level=messages.SUCCESS)

        # Дополнительно: выводим информацию о каждой обновленной подзадаче
        updated_titles = list(subtasks_to_update.values_list('title', flat=True))
        if len(updated_titles) <= 5:  # Показываем детали только если подзадач немного
            detail_message = f"Обновлены подзадачи: {', '.join(updated_titles)}"
            self.message_user(request, detail_message, level=messages.INFO)

    def show_done_subtasks(self, request, queryset):
        """Custom action для показа только подзадач в статусе Done"""
        # Получаем ID подзадач в статусе Done из выбранных
        done_subtasks = queryset.filter(status='DONE')

        if not done_subtasks.exists():
            self.message_user(
                request,
                "Среди выбранных подзадач нет ни одной в статусе 'Done'.",
                level=messages.WARNING
            )
            return

        # Формируем URL для фильтрации по статусу Done
        # Используем changelist_view с GET параметрами
        changelist_url = reverse('admin:task_manager_subtask_changelist')

        # Добавляем фильтр по статусу Done
        filtered_url = f"{changelist_url}?status__exact=DONE"

        # Показываем сообщение о количестве найденных подзадач
        done_count = done_subtasks.count()
        if done_count == 1:
            message = "Найдена 1 подзадача в статусе 'Done'. Применен фильтр."
        else:
            message = f"Найдено {done_count} подзадач в статусе 'Done'. Применен фильтр."

        self.message_user(request, message, level=messages.SUCCESS)

        # Перенаправляем на отфильтрованный список
        return HttpResponseRedirect(filtered_url)

    # Настройка отображения actions в админке
    mark_as_done.short_description = "Перевести выбранные подзадачи в статус 'Done'"
    show_done_subtasks.short_description = "Показать только подзадачи в статусе 'Done'"


@admin.register(Category, site=task_admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


# Also register with default admin (optional)
admin.site.register(Task, TaskAdmin)
admin.site.register(SubTask, SubTaskAdmin)
admin.site.register(Category, CategoryAdmin)