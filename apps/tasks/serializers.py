from django.utils import timezone
from rest_framework import serializers

from apps.projects.models import Project
from apps.users.models import User

from .models import Task


class UserAssigneeInfoSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "name")

    def get_name(self, obj: User) -> str:
        full_name = (obj.first_name or "").strip()
        if not full_name and obj.last_name:
            full_name = (obj.last_name or "").strip()
        return full_name or obj.email


class TaskSerializer(serializers.ModelSerializer):
    assignee = UserAssigneeInfoSerializer(read_only=True)
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "project",
            "due_date",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "project")


class TaskCreateSerializer(serializers.ModelSerializer):
    assignee_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID пользователя-исполнителя (assignee).",
    )
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        help_text="ID проекта.",
    )

    class Meta:
        model = Task
        fields = (
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "project",
            "due_date",
        )
        extra_kwargs = {
            "due_date": {"required": False, "allow_null": True},
            "description": {"required": False, "allow_blank": True},
        }

    def create(self, validated_data):
        assignee_id = validated_data.pop("assignee_id", None)
        # due_date может прийти как timezone-naive строка, но DRF сам конвертирует.
        if (
            "due_date" in validated_data
            and validated_data["due_date"]
            and timezone.is_naive(validated_data["due_date"])
        ):
            validated_data["due_date"] = timezone.make_aware(validated_data["due_date"])

        if assignee_id is not None:
            validated_data["assignee_id"] = assignee_id
        return Task.objects.create(**validated_data)

    def update(self, instance, validated_data):
        assignee_id = validated_data.pop("assignee_id", None)
        if (
            "due_date" in validated_data
            and validated_data["due_date"]
            and timezone.is_naive(validated_data["due_date"])
        ):
            validated_data["due_date"] = timezone.make_aware(validated_data["due_date"])

        if assignee_id is not None:
            validated_data["assignee_id"] = assignee_id

        return super().update(instance, validated_data)
