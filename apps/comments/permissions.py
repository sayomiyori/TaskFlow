from typing import Any

from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.tasks.models import Task
from apps.users.models import User
from .models import Comment


class IsAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, "role", None) == User.Role.ADMIN or user.is_superuser)
        )

    def has_object_permission(self, request, view, obj: Any) -> bool:
        return self.has_permission(request, view)


class IsProjectManager(BasePermission):
    """
    CRUD комментариев для задач в проектах, где user является owner.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if (
            not user
            or not user.is_authenticated
            or getattr(user, "role", None) != User.Role.MANAGER
        ):
            return False

        # При создании комментария проверяем принадлежность task проекту manager'а
        if request.method == "POST":
            task_id = request.data.get("task") or request.data.get("task_id")
            if not task_id:
                return False
            return Task.objects.filter(id=task_id, project__owner_id=user.id).exists()

        return True

    def has_object_permission(self, request, view, obj: Any) -> bool:
        user = request.user
        if (
            not user
            or not user.is_authenticated
            or getattr(user, "role", None) != User.Role.MANAGER
        ):
            return False

        if isinstance(obj, Comment):
            return obj.task.project.owner_id == user.id
        return False


class IsProjectMember(BasePermission):
    """
    Member читает комментарии только в своих проектах (CRUD комментов запрещен по ТЗ).
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if (
            not user
            or not user.is_authenticated
            or getattr(user, "role", None) != User.Role.MEMBER
        ):
            return False
        # CRUD комментов запрещён (только чтение)
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj: Any) -> bool:
        user = request.user
        if (
            not user
            or not user.is_authenticated
            or getattr(user, "role", None) != User.Role.MEMBER
        ):
            return False

        if request.method not in SAFE_METHODS:
            return False

        if isinstance(obj, Comment):
            project = obj.task.project
            return (
                project.owner_id == user.id
                or project.members.filter(id=user.id).exists()
            )
        return False


class IsAdminOrProjectManagerOrProjectMember(BasePermission):
    def has_permission(self, request, view) -> bool:
        return (
            IsAdmin().has_permission(request, view)
            or IsProjectManager().has_permission(request, view)
            or IsProjectMember().has_permission(request, view)
        )

    def has_object_permission(self, request, view, obj: Any) -> bool:
        return (
            IsAdmin().has_object_permission(request, view, obj)
            or IsProjectManager().has_object_permission(request, view, obj)
            or IsProjectMember().has_object_permission(request, view, obj)
        )
