import django_filters
from django_filters import rest_framework as drf_filters

from .models import Task


class TaskFilter(django_filters.FilterSet):
    status = drf_filters.CharFilter(field_name="status")
    priority = drf_filters.CharFilter(field_name="priority")
    assignee = drf_filters.NumberFilter(field_name="assignee__id")
    project = drf_filters.NumberFilter(field_name="project__id")

    # Диапазон по due_date
    due_date_after = drf_filters.DateTimeFilter(
        field_name="due_date", lookup_expr="gte"
    )
    due_date_before = drf_filters.DateTimeFilter(
        field_name="due_date", lookup_expr="lte"
    )

    class Meta:
        model = Task
        fields = [
            "status",
            "priority",
            "assignee",
            "project",
            "due_date_after",
            "due_date_before",
        ]
