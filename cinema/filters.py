import django_filters
from cinema.models import Movie, MovieSession


class MovieFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        field_name="title",
        lookup_expr="icontains",
        label="Title contains"
    )
    genres = django_filters.BaseInFilter(
        field_name="genres__id", label="Genre id"
    )
    actors = django_filters.BaseInFilter(
        field_name="actors__id", label="Actor id"
    )

    class Meta:
        model = Movie
        fields = (
            "title",
            "genres",
            "actors",
        )


class MovieSessionFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(
        field_name="show_time", lookup_expr="date", label="Date (YYYY-MM-DD)"
    )
    movie = django_filters.NumberFilter(
        field_name="movie__id", label="Movie ID"
    )

    class Meta:
        model = MovieSession
        fields = ("date", "movie")
