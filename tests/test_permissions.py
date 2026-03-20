import pytest

from conftest import ProjectFactory, TaskFactory
from apps.tasks.models import Task


@pytest.mark.django_db
def test_admin_can_access_all_projects(admin_client, manager_user):
    # Arrange
    ProjectFactory(owner=manager_user)
    ProjectFactory(owner=manager_user)

    # Act
    response = admin_client.get("/api/v1/projects/")

    # Assert
    assert response.status_code == 200


@pytest.mark.django_db
def test_manager_can_manage_own_project(manager_client, manager_user):
    # Arrange
    own_project = ProjectFactory(owner=manager_user)
    payload = {"name": "Updated own project", "description": own_project.description, "members": []}

    # Act
    response = manager_client.patch(f"/api/v1/projects/{own_project.id}/", payload, format="json")

    # Assert
    assert response.status_code == 200


@pytest.mark.django_db
def test_member_cannot_delete_task(member_client, member_user, manager_user):
    # Arrange
    project = ProjectFactory(owner=manager_user, members=[member_user])
    task = TaskFactory(project=project, assignee=member_user, status=Task.Status.TODO)

    # Act
    response = member_client.delete(f"/api/v1/tasks/{task.id}/")

    # Assert
    assert response.status_code == 403


@pytest.mark.django_db
def test_unauthenticated_user_gets_401(api_client):
    # Arrange
    url = "/api/v1/projects/"

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == 401
