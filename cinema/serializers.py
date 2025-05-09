from rest_framework import serializers

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket,
)
from .constants import (
    FIELDS_ACTOR,
    FIELDS_COMMON,
    FIELDS_SHOWTIME,
    FIELDS_CINEMA_HALL,
    FIELDS_GENRE,
    FIELDS_MOVIE,
    FIELDS_TAKEN,
    FIELDS_ORDER,
    FIELDS_TICKET,
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = FIELDS_GENRE


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = FIELDS_ACTOR


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = FIELDS_CINEMA_HALL


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = FIELDS_COMMON


class MovieListSerializer(MovieSerializer):
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )


class MovieDetailSerializer(MovieSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = FIELDS_COMMON


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = FIELDS_SHOWTIME


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )

    class Meta:
        model = MovieSession
        fields = FIELDS_MOVIE


class TicketsTakenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = FIELDS_TAKEN


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = TicketsTakenSerializer(
        many=True,
        read_only=True,
        source="tickets"
    )

    class Meta:
        model = MovieSession
        fields = FIELDS_SHOWTIME


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(many=False, read_only=True)

    class Meta:
        model = Ticket
        fields = FIELDS_TICKET


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = FIELDS_ORDER
