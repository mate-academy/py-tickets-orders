from django.urls import path
from .views import (
    MovieListView,
    MovieSessionListView,
    MovieSessionDetailView,
    OrderListCreateView,
)

urlpatterns = [
    path("movies/", MovieListView.as_view()),
    path("movie_sessions/", MovieSessionListView.as_view()),
    path("movie_sessions/<int:pk>/", MovieSessionDetailView.as_view()),
    path("orders/", OrderListCreateView.as_view()),
]
