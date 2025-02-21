from datetime import datetime, timedelta

from django.utils.timezone import make_aware
from rest_framework.exceptions import ValidationError


def _filter_by_date(queryset, date):
    try:
        start_date = make_aware(datetime.strptime(date, "%Y-%m-%d"))
        end_date = start_date + timedelta(days=1)
        return queryset.filter(
            show_time__gte=start_date,
            show_time__lt=end_date,
        )
    except ValueError:
        raise ValidationError("Invalid date format. Use YYYY-MM-DD")


def _filter_by_movie_id(queryset, movies):
    movie_ids = [int(movie) for movie in movies.split(",")]
    return queryset.filter(movie_id__in=movie_ids)


def _filter_by_actor_id(queryset, actors):
    actors_ids = [int(actor_id) for actor_id in actors.split(",")]
    return queryset.filter(
        actors__id__in=actors_ids).order_by("actors")


def _filter_by_genre_id(queryset, genres):
    genres_ids = [int(genre_id) for genre_id in genres.split(",")]
    return queryset.filter(
        genres__id__in=genres_ids).order_by("genres")


def _filter_by_movie_title(queryset, movie_title):
    return queryset.filter(title__icontains=movie_title)
