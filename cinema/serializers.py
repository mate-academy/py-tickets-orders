from typing import Any

from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

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

    def validate_rows(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError(
                "Number of rows must be a positive integer."
            )
        return value

    def validate_seats_in_row(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError(
                "Number of seats in a row must be a positive integer."
            )
        return value


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


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
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


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
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
        )


class MovieSessionListAvailableSerializer(MovieSessionListSerializer):
    tickets_available = serializers.SerializerMethodField()

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

    def get_tickets_available(self, obj: MovieSession) -> int:
        if hasattr(obj, "tickets_available"):
            return obj.tickets_available
        return obj.cinema_hall.capacity - obj.tickets.count()


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj: MovieSession) -> list[dict]:
        return [
            {"row": ticket.row, "seat": ticket.seat}
            for ticket in obj.tickets.all()
        ]


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        movie_session = attrs["movie_session"]
        row = attrs["row"]
        seat = attrs["seat"]
        cinema_hall = movie_session.cinema_hall

        if not (1 <= row <= cinema_hall.rows):
            raise serializers.ValidationError(
                {"row": f"Row number must be between 1 and "
                        f"{cinema_hall.rows}."}
            )

        if not (1 <= seat <= cinema_hall.seats_in_row):
            raise serializers.ValidationError(
                {
                    "seat": f"Seat number must be between 1 and "
                            f"{cinema_hall.seats_in_row}."
                }
            )

        return attrs

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")
        validators = [
            UniqueTogetherValidator(
                queryset=Ticket.objects.all(),
                fields=("movie_session", "row", "seat")
            )
        ]


class TicketListSerializer(TicketSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(read_only=False, many=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> Order:
        tickets = validated_data.pop("tickets")
        order = Order.objects.create(**validated_data)
        for ticket in tickets:
            Ticket.objects.create(order=order, **ticket)
        return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(read_only=True, many=True)
