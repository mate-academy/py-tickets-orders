import django_filters
from cinema.models import MovieSession, Movie


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class MovieSessionFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(
        field_name="show_time", lookup_expr="date"
    )
    movie = django_filters.NumberFilter(field_name="movie__id")

    class Meta:
        model = MovieSession
        fields = ("date", "movie", )


class MovieFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        field_name="title", lookup_expr="icontains"
    )
    actors = NumberInFilter(
        field_name="actors__id", lookup_expr="in", distinct=True
    )
    genres = NumberInFilter(
        field_name="genres__id", lookup_expr="in", distinct=True
    )

    class Meta:
        model = Movie
        fields = ("title", "actors", "genres")
