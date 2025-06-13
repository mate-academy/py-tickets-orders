import django_filters

from cinema.models import Movie, MovieSession


class MovieSessionFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(field_name="show_time", lookup_expr="date")
    movie = django_filters.NumberFilter(field_name="movie__id")

    class Meta:
        model = MovieSession
        fields = ["date", "movie"]
