from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.comments.urls import register_router as register_comments
from apps.projects.urls import register_router as register_projects
from apps.tasks.urls import register_router as register_tasks

router = DefaultRouter()
register_projects(router)
register_tasks(router)
register_comments(router)

urlpatterns = [
    path("admin/", admin.site.urls),
    # Swagger/OpenAPI
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    # API v1
    path("api/v1/", include(router.urls)),
    path("api/v1/", include("apps.users.urls")),
]
