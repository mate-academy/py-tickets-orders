import django_filters

from cinema.models import Movie, MovieSession


class MovieFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name="title",
                                      lookup_expr="icontains")

    class NumberInFilter(
            django_filters.BaseInFilter,
            django_filters.NumberFilter):
        pass

    genres = NumberInFilter(field_name="genres", lookup_expr="in")
    actors = NumberInFilter(field_name="actors", lookup_expr="in")

    class Meta:
        model = Movie
        fields = ["title", "actors", "genres"]


class MovieSessionFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(field_name="show_time",
                                     lookup_expr="date")
    movie = django_filters.NumberFilter(field_name="movie")

    class Meta:
        model = MovieSession
        fields = ["date", "movie"]
