from .views import ProjectViewSet


def register_router(router):
    router.register(r"projects", ProjectViewSet, basename="projects")
