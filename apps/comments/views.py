from django.db.models import Q
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.viewsets import ModelViewSet

from apps.comments.permissions import IsAdminOrProjectManagerOrProjectMember
from apps.users.models import User

from .models import Comment
from .serializers import CommentSerializer


class CommentViewSet(ModelViewSet):
    """
    CRUD комментариев к задачам.

    - Admin: полный доступ
    - Manager: CRUD комментариев в задачах своих проектов
    - Member: чтение комментариев в проектах, где состоит
    """

    serializer_class = CommentSerializer
    permission_classes = (IsAdminOrProjectManagerOrProjectMember,)

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Comment.objects.none()

        base_qs = Comment.objects.select_related("author", "task__project")

        if getattr(user, "role", None) == User.Role.ADMIN or user.is_superuser:
            return base_qs

        if getattr(user, "role", None) == User.Role.MANAGER:
            return base_qs.filter(task__project__owner_id=user.id)

        return base_qs.filter(
            Q(task__project__owner_id=user.id) | Q(task__project__members__id=user.id)
        ).distinct()

    @extend_schema(
        tags=["Comments"],
        description="Создать комментарий к задаче.",
        request=CommentSerializer,
        responses=CommentSerializer,
        examples=[
            OpenApiExample(
                "Create comment example",
                value={"text": "Looks good.", "task": 1},
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Comments"], description="Список комментариев.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Comments"], description="Получить комментарий по ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Comments"],
        description="Обновить комментарий.",
        request=CommentSerializer,
        responses=CommentSerializer,
        examples=[
            OpenApiExample(
                "Update comment example", value={"text": "Updated comment", "task": 1}
            )
        ],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["Comments"],
        description="Частично обновить комментарий.",
        request=CommentSerializer,
        responses=CommentSerializer,
        examples=[
            OpenApiExample(
                "Partial update example", value={"text": "Only text changed"}
            )
        ],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Comments"], description="Удалить комментарий.")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
