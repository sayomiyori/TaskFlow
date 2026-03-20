from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.viewsets import ModelViewSet

from apps.tasks.models import Task
from apps.tasks.permissions import IsAdminOrProjectManagerOrProjectMember
from apps.users.models import User

from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(ModelViewSet):
    """
    CRUD проектов.

    - Admin: полный доступ
    - Manager: CRUD своих проектов
    - Member: чтение проектов, в которых он состоит
    """

    serializer_class = ProjectSerializer
    permission_classes = (IsAdminOrProjectManagerOrProjectMember,)

    def get_queryset(self):
        user = self.request.user
        qs = Project.objects.none()
        if not user or not user.is_authenticated:
            return qs

        base_qs = Project.objects.select_related("owner").prefetch_related("members")
        if getattr(user, "role", None) == User.Role.MANAGER:
            base_qs = base_qs.filter(owner_id=user.id)
        elif getattr(user, "role", None) == User.Role.MEMBER:
            base_qs = base_qs.filter(
                Q(owner_id=user.id) | Q(members__id=user.id)
            ).distinct()

        return base_qs.annotate(
            todo_count=Count("tasks", filter=Q(tasks__status=Task.Status.TODO)),
            in_progress_count=Count(
                "tasks", filter=Q(tasks__status=Task.Status.IN_PROGRESS)
            ),
            review_count=Count("tasks", filter=Q(tasks__status=Task.Status.REVIEW)),
            done_count=Count("tasks", filter=Q(tasks__status=Task.Status.DONE)),
        )

    @extend_schema(
        tags=["Projects"],
        description="Создать проект.",
        request=ProjectSerializer,
        responses=ProjectSerializer,
        examples=[
            OpenApiExample(
                "Create project example",
                value={
                    "name": "New Project",
                    "description": "First project",
                    "members": [],
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Projects"], description="Получить список проектов.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Projects"], description="Получить проект по ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Projects"],
        description="Обновить проект.",
        request=ProjectSerializer,
        responses=ProjectSerializer,
        examples=[
            OpenApiExample(
                "Update project example",
                value={
                    "name": "Updated Project",
                    "description": "New description",
                    "members": [],
                },
            )
        ],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["Projects"],
        description="Частично обновить проект.",
        request=ProjectSerializer,
        responses=ProjectSerializer,
        examples=[
            OpenApiExample(
                "Partial update example",
                value={"description": "Only description changed"},
            )
        ],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Projects"], description="Удалить проект.")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
