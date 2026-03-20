from typing import Any

from django.db.models import Q
from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.users.models import User
from .models import Task
from apps.projects.models import Project


class IsAdmin(BasePermission):
    """
    Полный доступ к любым ресурсам.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, "role", None) == User.Role.ADMIN or user.is_superuser)
        )


def _user_is_project_owner(user: User, project: Project) -> bool:
    return project.owner_id == user.id


def _user_is_project_member(user: User, project: Project) -> bool:
    return project.owner_id == user.id or project.members.filter(id=user.id).exists()


class IsProjectManager(BasePermission):
    """
    CRUD задач в "своих" проектах (project.owner == user).
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "role", None) != User.Role.MANAGER:
            return False

        # Для create/update задач нужен project из request.data.
        # Для создания/обновления проектов object пока отсутствует — тогда
        # ключа `project` в data обычно нет, и мы не валидируем владение тут.
        if request.method not in SAFE_METHODS and request.method in ("POST", "PUT", "PATCH"):
            project_id = request.data.get("project") or request.data.get("project_id")
            if project_id:
                return Project.objects.filter(id=project_id, owner_id=user.id).exists()
            return True

        return True

    def has_object_permission(self, request, view, obj: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "role", None) != User.Role.MANAGER:
            return False

        if isinstance(obj, Task):
            return _user_is_project_owner(user, obj.project)
        if isinstance(obj, Project):
            return _user_is_project_owner(user, obj)

        return False


class IsProjectMember(BasePermission):
    """
    чтение + обновление assigned задач.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "role", None) != User.Role.MEMBER:
            return False

        # create запрещаем членам по требованиям
        if request.method not in SAFE_METHODS and request.method == "POST":
            return False
        return True

    def has_object_permission(self, request, view, obj: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "role", None) != User.Role.MEMBER:
            return False

        # READ: разрешено только если пользователь состоит в проекте
        if request.method in SAFE_METHODS:
            if isinstance(obj, Task):
                return _user_is_project_member(user, obj.project)
            if isinstance(obj, Project):
                return _user_is_project_member(user, obj)
            return False

        # UPDATE (PUT/PATCH): только assigned задачам пользователя
        if request.method in ("PUT", "PATCH"):
            if isinstance(obj, Task):
                return obj.assignee_id == user.id and _user_is_project_member(user, obj.project)

        return False


class IsAdminOrProjectManagerOrProjectMember(BasePermission):
    """
    DRF по умолчанию комбинирует permissions через AND,
    поэтому используем OR-обертку для согласования требований.
    """

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

