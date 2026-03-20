from datetime import timedelta

import factory
import pytest
from django.utils import timezone
from factory.django import DjangoModelFactory
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.comments.models import Comment
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.users.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = User.Role.MEMBER

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        raw = extracted or "StrongPassword123"
        obj.set_password(raw)
        if create:
            obj.save(update_fields=["password"])


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")
    description = factory.Faker("sentence")
    owner = factory.SubFactory(UserFactory, role=User.Role.MANAGER)

    @factory.post_generation
    def members(obj, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for member in extracted:
            obj.members.add(member)


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Sequence(lambda n: f"Task {n}")
    description = factory.Faker("sentence")
    status = Task.Status.TODO
    priority = Task.Priority.MEDIUM
    assignee = factory.SubFactory(UserFactory, role=User.Role.MEMBER)
    project = factory.SubFactory(ProjectFactory)
    due_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    text = factory.Faker("sentence")
    author = factory.SubFactory(UserFactory, role=User.Role.MEMBER)
    task = factory.SubFactory(TaskFactory)


def _auth_client(user: User) -> APIClient:
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return UserFactory(role=User.Role.ADMIN, is_superuser=True, is_staff=True)


@pytest.fixture
def manager_user(db):
    return UserFactory(role=User.Role.MANAGER)


@pytest.fixture
def member_user(db):
    return UserFactory(role=User.Role.MEMBER)


@pytest.fixture
def admin_client(admin_user):
    return _auth_client(admin_user)


@pytest.fixture
def manager_client(manager_user):
    return _auth_client(manager_user)


@pytest.fixture
def member_client(member_user):
    return _auth_client(member_user)


@pytest.fixture
def db_setup(manager_user, member_user):
    project = ProjectFactory(owner=manager_user, members=[member_user])
    task_1 = TaskFactory(
        title="Fix auth bug",
        project=project,
        assignee=member_user,
        status=Task.Status.TODO,
        priority=Task.Priority.HIGH,
    )
    task_2 = TaskFactory(
        title="Refactor API docs",
        project=project,
        assignee=member_user,
        status=Task.Status.IN_PROGRESS,
        priority=Task.Priority.MEDIUM,
    )
    task_3 = TaskFactory(
        title="Deploy to staging",
        project=project,
        assignee=manager_user,
        status=Task.Status.DONE,
        priority=Task.Priority.CRITICAL,
    )
    return {"project": project, "tasks": [task_1, task_2, task_3], "manager": manager_user, "member": member_user}
