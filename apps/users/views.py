from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import LoginSerializer, RegisterSerializer


class RegisterAPIView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Auth"],
        description="Регистрация пользователя.",
        request=RegisterSerializer,
        responses={201: RegisterSerializer},
        examples=[
            OpenApiExample(
                "Register example",
                value={"email": "john@example.com", "password": "StrongPassword123", "name": "John"},
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {"id": user.id, "email": user.email, "name": user.first_name},
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Auth"],
        description="Логин пользователя и получение access/refresh JWT токенов.",
        request=LoginSerializer,
        responses={200: {"access": "string", "refresh": "string"}},
        examples=[
            OpenApiExample(
                "Login example",
                value={"email": "john@example.com", "password": "StrongPassword123"},
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(email=email).first()
        if not user or not user.check_password(password):
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)}, status=status.HTTP_200_OK)

