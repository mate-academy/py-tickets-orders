from django.db.models import QuerySet
from django.http import HttpRequest
from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from cinema.models import MovieSession, Movie


class FilterMovieSessionByDateAndMovie(filters.BaseFilterBackend):
    def filter_queryset(
            self, request: HttpRequest,
            queryset: QuerySet[MovieSession],
            view: ModelViewSet
    ) -> QuerySet[MovieSession]:
        date = request.query_params.get("date")
        movie = request.query_params.get("movie")

        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie__id=movie)

        return queryset


class FilterMovieViewSet(filters.BaseFilterBackend):
    def filter_queryset(
            self, request: HttpRequest,
            queryset: QuerySet[Movie],
            view: ModelViewSet
    ):
        actors = request.query_params.get("actors")
        genres = request.query_params.get("genres")
        title = request.query_params.get("title")

        if actors:
            actor_ids = actors.split(",")
            queryset = queryset.filter(actors__id__in=actor_ids)

        if genres:
            genre_ids = genres.split(",")
            queryset = queryset.filter(genres__id__in=genre_ids)

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset
