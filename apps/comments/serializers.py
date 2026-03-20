from rest_framework import serializers

from apps.tasks.models import Task
from apps.users.models import User

from .models import Comment


class UserShortSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "name")

    def get_name(self, obj: User) -> str:
        full_name = ((obj.first_name or "") + " " + (obj.last_name or "")).strip()
        return full_name or obj.email


class CommentSerializer(serializers.ModelSerializer):
    author = UserShortSerializer(read_only=True)
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all())

    class Meta:
        model = Comment
        fields = ("id", "text", "author", "task", "created_at")
        read_only_fields = ("id", "author", "created_at")

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["author"] = request.user
        return Comment.objects.create(**validated_data)
