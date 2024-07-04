from django.db import transaction
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


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieSessionSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "movie", "title", "cinema_hall", "show_time")

    def get_title(self, obj):
        return obj.movie.title


class MovieSessionListSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
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

    @staticmethod
    def get_tickets_available(obj):
        sold_tickets_count = Ticket.objects.filter(movie_session=obj).count()
        available_tickets = obj.cinema_hall.capacity - sold_tickets_count
        return available_tickets


class MovieSessionDetailSerializer(MovieSessionSerializer):
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    movie = MovieSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "movie",
            "cinema_hall",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "taken_places",
        )

    @staticmethod
    def get_taken_places(obj):
        tickets = Ticket.objects.filter(movie_session=obj)
        return [{"row": ticket.row, "seat": ticket.seat} for ticket in tickets]


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionDetailSerializer(many=False, read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)
    taken_place = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets", "taken_place")

    def get_taken_place(self, obj):
        tickets = obj.tickets.all()
        taken_places = []
        for ticket in tickets:
            taken_places.append({
                "row": ticket.row,
                "seat": ticket.seat,
                # Add any other fields you need from Ticket model
            })
        return taken_places

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order
