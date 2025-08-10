from rest_framework import serializers
from .models import Task, Category, SubTask
from django.utils import timezone



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class SubTaskSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = SubTask
        fields = ['id', 'title', 'description', 'status', 'deadline', 'created_at', 'owner']
        read_only_fields = ['created_at']

class SubTaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = ['title', 'description', 'task', 'status', 'deadline', 'created_at']
        read_only_fields = ['created_at']


class TaskSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source='owner.username', read_only=True)

    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    subtasks = SubTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'categories', 'category_ids',
            'status', 'deadline', 'created_at', 'subtasks', 'owner'
        ]
        read_only_fields = ['created_at', 'owner']

    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        task = Task.objects.create(**validated_data)

        if category_ids:
            categories = Category.objects.filter(id__in=category_ids)
            task.categories.set(categories)

        return task

    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category_ids', None)

        # Update task fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update categories if provided
        if category_ids is not None:
            categories = Category.objects.filter(id__in=category_ids)
            instance.categories.set(categories)

        return instance


class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

    def validate_name(self, value):
        # Базовая проверка уникальности среди не «удалённых» категорий
        qs = Category.objects.all()
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.filter(name=value).exists():
            raise serializers.ValidationError("Category with this name already exists.")
        return value


    def update(self, instance, validated_data):
        name = validated_data.get('name')
        if Category.objects.filter(name=name).exclude(id=instance.id).exists():
            raise serializers.ValidationError(
                "Category with this name already exists."
            )
        instance.name = name
        instance.save()
        return instance


class TaskDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for tasks with nested subtasks"""
    categories = CategorySerializer(many=True, read_only=True)
    subtasks = SubTaskSerializer(many=True, read_only=True)
    subtasks_count = serializers.SerializerMethodField()
    overdue = serializers.SerializerMethodField()
    owner = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'categories', 'status', 'deadline',
            'created_at', 'subtasks', 'subtasks_count', 'overdue', 'owner'
        ]
        read_only_fields = ['created_at', 'owner']

    def get_subtasks_count(self, obj):
        return obj.subtasks.count()

    def get_overdue(self, obj):
        return obj.deadline < timezone.now() and obj.status != 'DONE'

class TaskCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for task creation"""
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'deadline', 'category_ids']

    def validate_deadline(self, value):
        """Validate that deadline is not in the past"""
        if value < timezone.now():
            raise serializers.ValidationError(
                "Deadline cannot be in the past."
            )
        return value

    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        task = Task.objects.create(**validated_data)

        if category_ids:
            categories = Category.objects.filter(id__in=category_ids)
            task.categories.set(categories)

        return task
