# GitHub: описание и topics репозитория

Скопируй в **Settings → General** репозитория на GitHub (поле **Description** и блок **Topics**).

## Description (до 350 символов)

```text
Django REST + JWT collaborative task API with WebSockets (Channels), RabbitMQ events, FastAPI notifications, Docker Compose, PostgreSQL, Redis, Nginx.
```

Короче (альтернатива):

```text
Task management backend: Django REST API, JWT, Channels WebSockets, RabbitMQ, FastAPI consumer, Docker Compose.
```

## Topics (вставь по одному или через запятую в UI)

Рекомендуемый набор (≤20 тегов на GitHub):

`django` `djangorestframework` `fastapi` `rabbitmq` `postgresql` `redis` `docker-compose` `nginx` `websockets` `django-channels` `jwt` `rest-api` `python` `task-management` `event-driven` `openapi` `pytest`

## Через GitHub CLI

После `gh auth login` из корня репозитория:

```bash
gh repo edit -d "Django REST + JWT collaborative task API with WebSockets (Channels), RabbitMQ events, FastAPI notifications, Docker Compose, PostgreSQL, Redis, Nginx." \
  --add-topic django \
  --add-topic djangorestframework \
  --add-topic fastapi \
  --add-topic rabbitmq \
  --add-topic postgresql \
  --add-topic redis \
  --add-topic docker-compose \
  --add-topic nginx \
  --add-topic websockets \
  --add-topic django-channels \
  --add-topic jwt \
  --add-topic rest-api \
  --add-topic python \
  --add-topic task-management \
  --add-topic event-driven \
  --add-topic openapi \
  --add-topic pytest
```

На Windows PowerShell удобнее одной строкой:

```powershell
gh repo edit -d "Django REST + JWT collaborative task API with WebSockets (Channels), RabbitMQ events, FastAPI notifications, Docker Compose, PostgreSQL, Redis, Nginx." --add-topic django --add-topic djangorestframework --add-topic fastapi --add-topic rabbitmq --add-topic postgresql --add-topic redis --add-topic docker-compose --add-topic nginx --add-topic websockets --add-topic django-channels --add-topic jwt --add-topic rest-api --add-topic python --add-topic task-management --add-topic event-driven --add-topic openapi --add-topic pytest
```
