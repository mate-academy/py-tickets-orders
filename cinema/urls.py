from rest_framework.routers import DefaultRouter
from .views import (
    MovieViewSet, MovieSessionViewSet, OrderViewSet
)

app_name = "cinema"

router = DefaultRouter()
router.register(r"movies", MovieViewSet, basename="movie")
router.register(
    r"movie_sessions", MovieSessionViewSet,
    basename="movie-session"
)
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = router.urls
