from django.db.models import Q
from django_filters import rest_framework as filters

from cinema.models import MovieSession, Movie


class MovieSessionFilter(filters.FilterSet):
    date = filters.DateFilter(field_name="show_time__date")
    movie = filters.NumberFilter(field_name="movie_id")

    class Meta:
        model = MovieSession
        fields = ["movie", "date"]


class MovieFilter(filters.FilterSet):
    title = filters.CharFilter(
        field_name="title",
        lookup_expr="icontains",
    )
    genres = filters.BaseInFilter(
        field_name="genres__id",
        lookup_expr="in",
    )
    actors = filters.NumberFilter(
        field_name="actors__id",
    )

    class Meta:
        model = Movie
        fields = ["title", "genres", "actors"]
