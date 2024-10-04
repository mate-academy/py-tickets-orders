import django_filters
from django.db.models import Q, QuerySet

from cinema.models import Movie, MovieSession


class MovieFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    genres = django_filters.BaseInFilter(field_name="genres__id")
    actors = django_filters.BaseInFilter(field_name="actors__id")

    class Meta:
        model = Movie
        fields = ["title", "genres", "actors"]


class MovieSessionFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(
        field_name="show_time",
        lookup_expr="date"
    )
    movie = django_filters.NumberFilter(field_name="movie__id")

    class Meta:
        model = MovieSession
        fields = ["date", "movie"]
