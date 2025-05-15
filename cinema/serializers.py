from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
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
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "tickets_available"
        )


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class TicketSerializerForOrderCreate(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")


class TicketListSerializer(TicketSerializer):
    movie_session = MovieSessionListSerializer()

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = TicketSerializer(many=True, source="tickets")

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializerForOrderCreate(many=True)

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        movie_session = tickets_data[0]["movie_session"]
        requested_seats = {
            (
                ticket["row"],
                ticket["seat"]
            ) for ticket in tickets_data
        }

        existing_seats = set(
            Ticket.objects.filter(
                movie_session=movie_session,
                row__in=[row for row, _ in requested_seats],
                seat__in=[seat for _, seat in requested_seats],
            ).values_list("row", "seat")
        )

        overlapping = requested_seats & existing_seats
        if overlapping:
            raise ValidationError({
                "tickets": f"The seats are already taken: {list(overlapping)}"
            })

        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")
