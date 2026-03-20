from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
def test_register_success(api_client):
    # Arrange
    payload = {
        "email": "newuser@example.com",
        "password": "StrongPassword123",
        "name": "New User",
    }

    # Act
    response = api_client.post("/api/v1/auth/register/", payload, format="json")

    # Assert
    assert response.status_code == 201


@pytest.mark.django_db
def test_register_duplicate_email(api_client):
    # Arrange
    payload = {
        "email": "dup@example.com",
        "password": "StrongPassword123",
        "name": "Dup User",
    }
    api_client.post("/api/v1/auth/register/", payload, format="json")

    # Act
    response = api_client.post("/api/v1/auth/register/", payload, format="json")

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_login_success(api_client):
    # Arrange
    register_payload = {
        "email": "loginok@example.com",
        "password": "StrongPassword123",
        "name": "Login User",
    }
    api_client.post("/api/v1/auth/register/", register_payload, format="json")

    # Act
    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": register_payload["email"], "password": register_payload["password"]},
        format="json",
    )

    # Assert
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_wrong_password(api_client):
    # Arrange
    register_payload = {
        "email": "loginbad@example.com",
        "password": "StrongPassword123",
        "name": "Login Bad",
    }
    api_client.post("/api/v1/auth/register/", register_payload, format="json")

    # Act
    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": register_payload["email"], "password": "WrongPassword123"},
        format="json",
    )

    # Assert
    assert response.status_code == 401


@pytest.mark.django_db
def test_refresh_token(api_client):
    # Arrange
    register_payload = {
        "email": "refresh@example.com",
        "password": "StrongPassword123",
        "name": "Refresh User",
    }
    api_client.post("/api/v1/auth/register/", register_payload, format="json")
    login_response = api_client.post(
        "/api/v1/auth/login/",
        {"email": register_payload["email"], "password": register_payload["password"]},
        format="json",
    )

    # Act
    response = api_client.post(
        "/api/v1/auth/refresh/",
        {"refresh": login_response.data["refresh"]},
        format="json",
    )

    # Assert
    assert response.status_code == 200


@pytest.mark.django_db
def test_access_expired(api_client, member_user):
    # Arrange
    refresh = RefreshToken.for_user(member_user)
    expired_access = refresh.access_token
    expired_access.set_exp(
        from_time=timezone.now() - timedelta(minutes=10), lifetime=timedelta(seconds=1)
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(expired_access)}")

    # Act
    response = api_client.get("/api/v1/projects/")

    # Assert
    assert response.status_code == 401
