from django.db import transaction
from rest_framework import serializers

from cinema.models import (Actor, CinemaHall, Genre, Movie, MovieSession,
                           Order, Ticket)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ["id", "first_name", "last_name", "full_name"]


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ["id", "name", "rows", "seats_in_row", "capacity"]


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ["id", "title", "description", "duration", "genres", "actors"]


class MovieListSerializer(MovieSerializer):
    genres = serializers.SlugRelatedField(
        slug_field="name", many=True, read_only=True
    )
    actors = serializers.SlugRelatedField(
        slug_field="full_name", many=True, read_only=True
    )


class MovieDetailSerializer(MovieSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ["id", "title", "description", "duration", "genres", "actors"]


class MovieSessionSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
    movie = serializers.PrimaryKeyRelatedField(queryset=Movie.objects.all())
    cinema_hall = serializers.PrimaryKeyRelatedField(
        queryset=CinemaHall.objects.all()
    )

    class Meta:
        model = MovieSession
        fields = [
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "movie",
            "cinema_hall",
        ]


class MovieSessionListSerializer(MovieSessionSerializer):
    tickets_available = serializers.IntegerField()

    class Meta:
        model = MovieSession
        fields = [
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "tickets_available",
        ]


class TicketListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["row", "seat"]


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    taken_places = TicketListSerializer(
        many=True, source="tickets", read_only=True
    )

    class Meta:
        model = MovieSession
        fields = ["id", "show_time", "movie", "cinema_hall", "taken_places"]


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "row", "seat", "movie_session"]

    def validate(self, data: dict) -> dict:
        movie_session = data.get("movie_session")
        row = data.get("row")
        seat = data.get("seat")

        if not (1 <= row <= movie_session.cinema_hall.rows):
            raise serializers.ValidationError(
                {
                    "row": (
                        "Row number must be in range: "
                        f"(1, {movie_session.cinema_hall.rows})."
                    )
                }
            )

        if not (1 <= seat <= movie_session.cinema_hall.seats_in_row):
            raise serializers.ValidationError(
                {
                    "seat": (
                        "Seat number must be in range: "
                        f"(1, {movie_session.cinema_hall.seats_in_row})."
                    )
                }
            )

        if Ticket.objects.filter(
            movie_session=movie_session, row=row, seat=seat
        ).exists():
            raise serializers.ValidationError(
                f"Seat {seat} in row {row} is already taken."
            )

        return data


class TicketDetailSerializer(TicketSerializer):
    movie_session = MovieSessionSerializer()


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, required=True)

    class Meta:
        model = Order
        fields = ["id", "tickets", "created_at"]

    def create(self, validated_data: dict) -> Order:
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)

            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)

            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketDetailSerializer(many=True)
