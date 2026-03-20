import pytest

from conftest import TaskFactory
from apps.tasks.models import Task


@pytest.mark.django_db
def test_create_task_as_manager(manager_client, db_setup):
    # Arrange
    payload = {
        "title": "Manager created task",
        "description": "Created by manager",
        "status": Task.Status.TODO,
        "priority": Task.Priority.HIGH,
        "assignee_id": db_setup["member"].id,
        "project": db_setup["project"].id,
    }

    # Act
    response = manager_client.post("/api/v1/tasks/", payload, format="json")

    # Assert
    assert response.status_code == 201


@pytest.mark.django_db
def test_create_task_as_member(member_client, db_setup):
    # Arrange
    payload = {
        "title": "Member cannot create",
        "description": "Forbidden",
        "status": Task.Status.TODO,
        "priority": Task.Priority.MEDIUM,
        "assignee_id": db_setup["member"].id,
        "project": db_setup["project"].id,
    }

    # Act
    response = member_client.post("/api/v1/tasks/", payload, format="json")

    # Assert
    assert response.status_code == 403


@pytest.mark.django_db
def test_list_tasks_with_filters(manager_client, db_setup):
    # Arrange
    target = db_setup["tasks"][0]
    url = (
        f"/api/v1/tasks/?status={target.status}&priority={target.priority}"
        f"&assignee={target.assignee_id}&project={target.project_id}"
    )

    # Act
    response = manager_client.get(url)

    # Assert
    assert all(item["id"] == target.id for item in response.data["results"])


@pytest.mark.django_db
def test_list_tasks_pagination(manager_client, db_setup):
    # Arrange
    for i in range(25):
        TaskFactory(project=db_setup["project"], assignee=db_setup["member"], title=f"Paginated task {i}")

    # Act
    response = manager_client.get("/api/v1/tasks/")

    # Assert
    assert len(response.data["results"]) == 20


@pytest.mark.django_db
def test_update_task_status(manager_client, db_setup):
    # Arrange
    task = db_setup["tasks"][0]
    payload = {
        "title": task.title,
        "description": task.description,
        "status": Task.Status.REVIEW,
        "priority": task.priority,
        "project": task.project_id,
        "assignee_id": task.assignee_id,
        "due_date": task.due_date.isoformat().replace("+00:00", "Z"),
    }

    # Act
    response = manager_client.put(f"/api/v1/tasks/{task.id}/", payload, format="json")

    # Assert
    assert response.status_code == 200


@pytest.mark.django_db
def test_search_tasks_by_title(manager_client, db_setup):
    # Arrange
    needle = "Unique Search Phrase"
    TaskFactory(project=db_setup["project"], assignee=db_setup["member"], title=needle)

    # Act
    response = manager_client.get(f"/api/v1/tasks/?search={needle}")

    # Assert
    assert any(item["title"] == needle for item in response.data["results"])


@pytest.mark.django_db
def test_ordering_by_priority(manager_client, db_setup):
    # Arrange
    TaskFactory(project=db_setup["project"], assignee=db_setup["member"], title="P1", priority=Task.Priority.CRITICAL)
    TaskFactory(project=db_setup["project"], assignee=db_setup["member"], title="P2", priority=Task.Priority.LOW)
    TaskFactory(project=db_setup["project"], assignee=db_setup["member"], title="P3", priority=Task.Priority.HIGH)

    # Act
    response = manager_client.get("/api/v1/tasks/?ordering=priority")
    priorities = [item["priority"] for item in response.data["results"]]

    # Assert
    assert priorities == sorted(priorities)
