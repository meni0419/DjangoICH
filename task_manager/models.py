from django.db import models
from django.utils import timezone

STATUS_CHOICES = [
    ('NEW', 'New'),
    ('IN_PROGRESS', 'In progress'),
    ('PENDING', 'Pending'),
    ('BLOCKED', 'Blocked'),
    ('DONE', 'Done'),
]


class CategoryQuerySet(models.QuerySet):
    def delete(self):
        # Soft delete для queryset
        now = timezone.now()
        return super().update(is_deleted=True, deleted_at=now)


class CategoryManager(models.Manager):
    def get_queryset(self):
        return CategoryQuerySet(self.model, using=self._db).filter(is_deleted=False)


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'task_manager_category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        constraints = [
            models.UniqueConstraint(fields=['name'], name='unique_category_name')
        ]

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def __str__(self):
        return self.name


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    categories = models.ManyToManyField('Category')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'task_manager_task'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['title'], name='unique_task_title')
        ]

    def __str__(self):
        return self.title


class SubTask(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'task_manager_subtask'
        verbose_name = 'SubTask'
        verbose_name_plural = 'SubTasks'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['title'], name='unique_subtask_title')
        ]

    def __str__(self):
        return self.title
