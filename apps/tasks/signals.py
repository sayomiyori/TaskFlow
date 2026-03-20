from typing import Any

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.comments.models import Comment
from apps.events.publisher import RabbitMQPublisher
from apps.tasks.models import Task

publisher = RabbitMQPublisher()


@receiver(pre_save, sender=Task)
def cache_previous_assignee(sender: Any, instance: Task, **kwargs: Any) -> None:
    if not instance.pk:
        instance._previous_assignee_id = None
        return
    previous = Task.objects.filter(pk=instance.pk).values("assignee_id").first()
    instance._previous_assignee_id = previous["assignee_id"] if previous else None


@receiver(post_save, sender=Task)
def publish_task_events(
    sender: Any, instance: Task, created: bool, **kwargs: Any
) -> None:
    base_payload = {
        "event_type": "task.created" if created else "task.updated",
        "task_id": instance.id,
        "project_id": instance.project_id,
        "actor_id": instance.assignee_id,
        "timestamp": timezone.now().isoformat(),
        "data": {
            "title": instance.title,
            "status": instance.status,
            "priority": instance.priority,
            "assignee_id": instance.assignee_id,
            "due_date": instance.due_date.isoformat() if instance.due_date else None,
        },
    }

    publisher.publish_event(base_payload["event_type"], base_payload)

    if not created:
        old_assignee = getattr(instance, "_previous_assignee_id", None)
        if old_assignee != instance.assignee_id:
            assigned_payload = {
                "event_type": "task.assigned",
                "task_id": instance.id,
                "project_id": instance.project_id,
                "actor_id": instance.assignee_id,
                "timestamp": timezone.now().isoformat(),
                "data": {
                    "old_assignee_id": old_assignee,
                    "new_assignee_id": instance.assignee_id,
                    "status": instance.status,
                },
            }
            publisher.publish_event("task.assigned", assigned_payload)


@receiver(post_save, sender=Comment)
def publish_comment_event(
    sender: Any, instance: Comment, created: bool, **kwargs: Any
) -> None:
    if not created:
        return
    project_id = (
        Task.objects.filter(pk=instance.task_id)
        .values_list("project_id", flat=True)
        .first()
    )
    payload = {
        "event_type": "task.commented",
        "task_id": instance.task_id,
        "project_id": project_id,
        "actor_id": instance.author_id,
        "timestamp": timezone.now().isoformat(),
        "data": {
            "comment_id": instance.id,
            "text": instance.text,
        },
    }
    publisher.publish_event("task.commented", payload)
