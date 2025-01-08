from django.db.models import Q
from django.db.models import OuterRef, Subquery
from django_filters import rest_framework as filters
from cinema.models import MovieSession, Movie, Actor
import logging


class MovieSessionFilter(filters.FilterSet):
    date = filters.DateFilter(field_name="show_time", lookup_expr="date")
    movie = filters.NumberFilter(field_name="movie__id")

    class Meta:
        model = MovieSession
        fields = ["date", "movie"]


logger = logging.getLogger(__name__)


class MovieFilter(filters.FilterSet):
    genres = filters.CharFilter(method="filter_by_genre_ids")
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")
    actors = filters.CharFilter(method="filter_by_actor_ids")

    class Meta:
        model = Movie
        fields = ["genres", "title", "actors"]

    def filter_by_genre_ids(self, queryset, name, value):
        genre_ids = [
            int(id.strip())
            for id in value.split(",")
            if id.strip().isdigit()
        ]
        return queryset.filter(genres__id__in=genre_ids)

    def filter_by_actor_ids(self, queryset, name, value):
        try:
            # Преобразуем значения в список ID
            actor_ids = [
                int(id.strip())
                for id in value.split(",")
                if id.strip().isdigit()
            ]
            return queryset.filter(actors__id__in=actor_ids)
        except ValueError as e:
            # Логируем ошибку для отладки
            logger.warning(f"Invalid actor ID input: '{value}'. Error: {e}")
            # Возвращаем пустой queryset, если данные некорректны
            return queryset.none()
