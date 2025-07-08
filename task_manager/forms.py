from django import forms
from django.utils import timezone
from .models import Task, SubTask, Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter category name...'
            })
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'categories', 'status', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter task title...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Enter task description...',
                'rows': 4
            }),
            'categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-checkbox'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-input',
                'type': 'datetime-local'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default deadline to tomorrow
        if not self.instance.pk:
            tomorrow = timezone.now() + timezone.timedelta(days=1)
            self.fields['deadline'].initial = tomorrow.strftime('%Y-%m-%dT%H:%M')

class SubTaskForm(forms.ModelForm):
    class Meta:
        model = SubTask
        fields = ['title', 'description', 'status', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter subtask title...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Enter subtask description...',
                'rows': 3
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-input',
                'type': 'datetime-local'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default deadline to tomorrow
        if not self.instance.pk:
            tomorrow = timezone.now() + timezone.timedelta(days=1)
            self.fields['deadline'].initial = tomorrow.strftime('%Y-%m-%dT%H:%M')