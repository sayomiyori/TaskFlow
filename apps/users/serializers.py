from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email пользователя.")
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        help_text="Пароль пользователя.",
    )
    name = serializers.CharField(help_text="Имя пользователя.")

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return email

    def create(self, validated_data):
        email = validated_data["email"]
        name = validated_data["name"]
        password = validated_data["password"]

        user = User(email=email, first_name=name, role=User.Role.MEMBER)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email пользователя.")
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Пароль пользователя.",
    )
