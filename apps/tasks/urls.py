from .views import TaskViewSet


def register_router(router):
    router.register(r"tasks", TaskViewSet, basename="tasks")

