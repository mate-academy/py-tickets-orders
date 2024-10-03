import django_filters
from django.db.models import Q

from cinema.models import Movie, MovieSession


class MovieFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    genres = django_filters.CharFilter(method="filter_genres")
    actors = django_filters.CharFilter(method="filter_actors")

    class Meta:
        model = Movie
        fields = ["title", "genres", "actors"]

    def filter_genres(self, queryset, name, value):
        if value:
            genre_names = value.split(",")
            query = Q()
            for genre_name in genre_names:
                query |= Q(genres__name__icontains=genre_name.strip())
            return queryset.filter(query)
        return queryset

    def filter_actors(self, queryset, name, value):
        if value:
            actor_names = value.split(",")
            query = Q()
            for actor_name in actor_names:
                if " " in actor_name.strip():
                    first_name, last_name = actor_name.strip().split()
                else:
                    first_name, last_name = actor_name.strip(), ""

                query |= (
                    Q(actors__first_name__icontains=first_name)
                    & Q(actors__last_name__icontains=last_name)
                )
            return queryset.filter(query)
        return queryset


class MovieSessionFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(
        field_name="show_time",
        lookup_expr="date"
    )
    movie = django_filters.NumberFilter(field_name="movie__id")

    class Meta:
        model = MovieSession
        fields = ["date", "movie"]
