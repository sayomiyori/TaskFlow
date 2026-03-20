from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from apps.users.models import User

from .filters import TaskFilter
from .models import Task
from .permissions import IsAdminOrProjectManagerOrProjectMember
from .serializers import TaskCreateSerializer, TaskSerializer


class TaskViewSet(ModelViewSet):
    """
    CRUD задач:
    - Admin: полный доступ
    - Manager: CRUD задач в проектах, где он является owner
    - Member: чтение + обновление только assigned задач
    """

    queryset = Task.objects.none()
    serializer_class = TaskSerializer
    permission_classes = (IsAdminOrProjectManagerOrProjectMember,)

    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_class = TaskFilter
    ordering_fields = ("created_at", "due_date", "priority")
    search_fields = ("title", "description")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TaskCreateSerializer
        return TaskSerializer

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Task.objects.none()

        base_qs = Task.objects.select_related("assignee", "project")

        if getattr(user, "role", None) == User.Role.ADMIN or user.is_superuser:
            return base_qs

        if getattr(user, "role", None) == User.Role.MANAGER:
            return base_qs.filter(project__owner_id=user.id)

        # Member
        return base_qs.filter(
            Q(project__owner_id=user.id) | Q(project__members__id=user.id)
        ).distinct()

    def perform_destroy(self, instance: Task) -> None:
        # Членам запрещаем удалять (по требованиям)
        if getattr(self.request.user, "role", None) == User.Role.MEMBER:
            raise PermissionDenied("Members cannot delete tasks.")
        super().perform_destroy(instance)

    @extend_schema(
        tags=["Tasks"],
        description="Создать задачу в проекте.",
        request=TaskCreateSerializer,
        responses=TaskSerializer,
        examples=[
            OpenApiExample(
                "Create task example",
                value={
                    "title": "Implement JWT auth",
                    "description": "Add JWT endpoints and protect resources.",
                    "status": "todo",
                    "priority": "high",
                    "assignee_id": 1,
                    "project": 1,
                    "due_date": "2026-03-30T12:00:00Z",
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=["Tasks"], description="Список задач с фильтрами/поиском/сортировкой."
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Tasks"], description="Получить задачу по ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Tasks"],
        description="Обновить задачу (можно обновлять assignee_id для manager/Admin).",
        request=TaskCreateSerializer,
        responses=TaskSerializer,
        examples=[
            OpenApiExample(
                "Update task example",
                value={
                    "title": "Implement JWT auth",
                    "description": "Add JWT endpoints and protect resources.",
                    "status": "in_progress",
                    "priority": "high",
                    "assignee_id": 1,
                    "project": 1,
                    "due_date": "2026-03-30T12:00:00Z",
                },
            )
        ],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["Tasks"],
        description="Частичное обновление задачи.",
        request=TaskCreateSerializer,
        responses=TaskSerializer,
        examples=[
            OpenApiExample(
                "Partial update example",
                value={"status": "review", "priority": "medium"},
            )
        ],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Tasks"], description="Удалить задачу.")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
