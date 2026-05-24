from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
    Ticket,
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors",
        )


class MovieListSerializer(MovieSerializer):
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )
    actors = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name",
    )


class MovieDetailSerializer(MovieSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors",
        )


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(
        source="movie.title",
        read_only=True,
    )
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name",
        read_only=True,
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity",
        read_only=True,
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "tickets_available",
        )


class TakenPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class MovieSessionMovieDetailSerializer(MovieSerializer):
    """Used inside MovieSessionDetailSerializer.
    Genres and actors as slug strings per test expectation."""
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )
    actors = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name",
    )

    class Meta:
        model = Movie
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors",
        )


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieSessionMovieDetailSerializer(
        many=False, read_only=True
    )
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = TakenPlaceSerializer(
        source="tickets",
        many=True,
        read_only=True,
    )

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
            "taken_places",
        )


class TicketMovieSessionSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(
        source="movie.title",
        read_only=True,
    )
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name",
        read_only=True,
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity",
        read_only=True,
    )

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
        )


class TicketSerializer(serializers.ModelSerializer):
    movie_session = TicketMovieSessionSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs: dict) -> dict:
        row: int = attrs["row"]
        seat: int = attrs["seat"]
        movie_session: MovieSession = attrs["movie_session"]
        hall: CinemaHall = movie_session.cinema_hall

        if not (1 <= row <= hall.rows):
            raise serializers.ValidationError(
                {
                    "row": (
                        f"row number must be in available range: "
                        f"(1, rows): (1, {hall.rows})"
                    )
                }
            )

        if not (1 <= seat <= hall.seats_in_row):
            raise serializers.ValidationError(
                {
                    "seat": (
                        f"seat number must be in available range: "
                        f"(1, seats_in_row): (1, {hall.seats_in_row})"
                    )
                }
            )

        if Ticket.objects.filter(
            movie_session=movie_session,
            row=row,
            seat=seat,
        ).exists():
            raise serializers.ValidationError(
                {
                    "seat": (
                        f"row: {row}, seat: {seat} — "
                        f"already taken for this session."
                    )
                }
            )

        return attrs


class OrderReadSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data: dict) -> Order:
        tickets_data: list[dict] = validated_data.pop("tickets")

        with transaction.atomic():
            order: Order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)

        return order
