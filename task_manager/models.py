from django.db import models
from django.utils import timezone

STATUS_CHOICES = [
    ('NEW', 'New'),
    ('IN_PROGRESS', 'In progress'),
    ('PENDING', 'Pending'),
    ('BLOCKED', 'Blocked'),
    ('DONE', 'Done'),
]


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

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
        constraints = [
            models.UniqueConstraint(
                fields=['title'],
                condition=models.Q(created_at__date=models.F('created_at__date')),
                name='unique_title_per_day'
            )
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

    def __str__(self):
        return self.title