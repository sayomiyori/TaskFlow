from .views import CommentViewSet


def register_router(router):
    router.register(r"comments", CommentViewSet, basename="comments")

