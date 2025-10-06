from rest_framework import serializers
from django.db import transaction
from django.core.exceptions import ValidationError

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket
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

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
        )


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketDetailSerializer(serializers.ModelSerializer):
    movie_session = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")

    def get_movie_session(self, obj):
        return {
            "id": obj.movie_session.id,
            "show_time": obj.movie_session.show_time,
            "movie_title": obj.movie_session.movie.title,
            "cinema_hall_name": obj.movie_session.cinema_hall.name,
            "cinema_hall_capacity": obj.movie_session.cinema_hall.capacity
        }


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True)

    class Meta:
        model = Order
        fields = ("tickets",)

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(
                user=self.context["request"].user,
                **validated_data
            )

            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)

            return order

    def validate_tickets(self, tickets):
        if not tickets:
            raise serializers.ValidationError(
                "At least one ticket is required."
            )

        for ticket_data in tickets:
            movie_session = ticket_data["movie_session"]
            row = ticket_data["row"]
            seat = ticket_data["seat"]

            if Ticket.objects.filter(
                movie_session=movie_session,
                row=row,
                seat=seat
            ).exists():
                raise serializers.ValidationError(
                    f"Seat {seat} in row {row} is already taken for "
                    f"this movie session."
                )

            cinema_hall = movie_session.cinema_hall
            if row < 1 or row > cinema_hall.rows:
                raise serializers.ValidationError(
                    f"Row must be between 1 and {cinema_hall.rows}."
                )
            if seat < 1 or seat > cinema_hall.seats_in_row:
                raise serializers.ValidationError(
                    f"Seat must be between 1 and {cinema_hall.seats_in_row}."
                )

        return tickets


class MovieSessionListWithTicketsSerializer(MovieSessionListSerializer):
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

    def get_tickets_available(self, obj):
        taken_tickets_count = Ticket.objects.filter(movie_session=obj).count()
        available = obj.cinema_hall.capacity - taken_tickets_count
        return max(0, available)


class MovieSessionDetailWithPlacesSerializer(MovieSessionDetailSerializer):
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj):
        tickets = obj.tickets.all()
        return [
            {"row": ticket.row, "seat": ticket.seat}
            for ticket in tickets
        ]
