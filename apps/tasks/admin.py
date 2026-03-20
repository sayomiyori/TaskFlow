from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "priority", "project", "assignee", "due_date")
    list_filter = ("status", "priority")
    search_fields = ("title", "project__name", "assignee__email")
