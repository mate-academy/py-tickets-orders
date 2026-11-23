import django_filters as filters

from cinema.models import Movie, MovieSession


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class MovieFilter(filters.FilterSet):
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")
    genres = NumberInFilter(field_name="genres__id", lookup_expr="in")
    actors = NumberInFilter(field_name="actors__id", lookup_expr="in")

    class Meta:
        model = Movie
        fields = ("title", "genres", "actors")


class MovieSessionFilter(filters.FilterSet):
    date = filters.DateFilter(field_name="show_time__date")
    movie = filters.NumberFilter(field_name="movie_id")

    class Meta:
        model = MovieSession
        fields = ("date", "movie")
