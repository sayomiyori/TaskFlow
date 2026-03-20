from rest_framework import serializers

from apps.users.models import User
from .models import Project


class ProjectOwnerSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "name")

    def get_name(self, obj: User) -> str:
        full_name = ((obj.first_name or "") + " " + (obj.last_name or "")).strip()
        return full_name or obj.email


class ProjectSerializer(serializers.ModelSerializer):
    owner = ProjectOwnerSerializer(read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
        allow_empty=True,
    )

    todo_count = serializers.IntegerField(read_only=True, allow_null=True)
    in_progress_count = serializers.IntegerField(read_only=True, allow_null=True)
    review_count = serializers.IntegerField(read_only=True, allow_null=True)
    done_count = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "description",
            "owner",
            "members",
            "todo_count",
            "in_progress_count",
            "review_count",
            "done_count",
        )

    def create(self, validated_data):
        members = validated_data.pop("members", [])
        request = self.context.get("request")
        user = getattr(request, "user", None)
        project = Project.objects.create(owner=user, **validated_data)
        if members:
            project.members.set(members)
        return project

    def update(self, instance, validated_data):
        members = validated_data.pop("members", None)
        # owner управляется на уровне permission/вью; не даем менять в serializer.
        validated_data.pop("owner", None)
        project = super().update(instance, validated_data)
        if members is not None:
            project.members.set(members)
        return project
