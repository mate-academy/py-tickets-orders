import django_filters

from cinema.models import Movie, MovieSession


class MovieFilterSet(django_filters.FilterSet):
    actors = django_filters.NumberFilter(field_name="actors__id")
    genres = django_filters.CharFilter(
        field_name="genres__name",
        lookup_expr="icontains",
    )
    title = django_filters.CharFilter(
        field_name="title",
        lookup_expr="icontains",
    )

    class Meta:
        model = Movie
        fields = ["actors", "genres", "title"]


class MovieSessionFilterSet(django_filters.FilterSet):
    date = django_filters.DateFilter(
        field_name="show_time",
        lookup_expr="date",
    )
    movie = django_filters.NumberFilter(field_name="movie_id")

    class Meta:
        model = MovieSession
        fields = ["date", "movie"]
