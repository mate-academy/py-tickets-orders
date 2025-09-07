import django_filters
from cinema.models import Movie, MovieSession, Genre, Actor


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class MovieFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        field_name="title",
        lookup_expr="icontains"
    )
    genres = NumberInFilter(field_name="genres__id", lookup_expr="in")
    actors = NumberInFilter(field_name="actors__id", lookup_expr="in")

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
