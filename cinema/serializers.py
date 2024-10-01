from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.pagination import PageNumberPagination

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


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
            "taken_places",
        )

    def get_taken_places(self, movie_session: MovieSession) -> list[dict]:
        return [
            {
                "row": ticket.row,
                "seat": ticket.seat
            }
            for ticket in movie_session.tickets.all()
        ]


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(read_only=False)

    class Meta:
        model = Ticket
        fields = ["id", "row", "seat", "movie_session"]


class OrderSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 3


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True,
        read_only=False,
        allow_empty=False,
    )

    class Meta:
        model = Order
        fields = ["id", "tickets", "created_at"]


class TicketCreateSerializer(TicketSerializer):
    movie_session = serializers.PrimaryKeyRelatedField(
        queryset=MovieSession.objects.all()
    )

    def validate(self, validate_data: dict):
        movie_session = validate_data.pop("movie_session")
        row = validate_data.pop("row")
        seat = validate_data.pop("seat")

        if Ticket.objects.filter(
                movie_session=movie_session, row=row, seat=seat
        ).exists():
            raise serializers.ValidationError(
                f"Seat {seat} in row {row} is already taken "
                f"for this movie session."
            )

        cinema_hall = movie_session.cinema_hall
        if row < 1 or row > cinema_hall.rows:
            raise serializers.ValidationError(
                f"Row {row} is not valid for this cinema hall."
                f"Must be in range [1, {cinema_hall.rows}]"
            )
        if seat < 1 or seat > cinema_hall.seats_in_row:
            raise serializers.ValidationError(
                f"Seat {seat} is not valid for this cinema hall."
                f"Must be in range [1, {cinema_hall.seats_in_row}]"
            )

        return validate_data


class OrderCreateSerializer(OrderSerializer):
    tickets = TicketCreateSerializer(
        many=True,
        read_only=False,
        allow_empty=False
    )

    def create(self, validated_data: dict) -> Order:
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)

            return order
