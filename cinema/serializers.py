from rest_framework import serializers
from django.utils import timezone
from datetime import datetime
from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class CinemaHallSerializer(serializers.ModelSerializer):
    capacity = serializers.ReadOnlyField()

    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieListSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    actors = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")

    def get_actors(self, obj):
        return [f"{actor.first_name} {actor.last_name}" for actor in obj.actors.all()]


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")

    def validate_show_time(self, value):
        # Конвертуємо наївний datetime у timezone-aware, якщо потрібно
        if value and not timezone.is_aware(value):
            value = timezone.make_aware(value, timezone=timezone.utc)
        return value


class MovieSessionListSerializer(serializers.ModelSerializer):
    taken_places = serializers.SerializerMethodField()
    tickets_available = serializers.SerializerMethodField()
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(source="cinema_hall.name", read_only=True)
    cinema_hall_capacity = serializers.IntegerField(source="cinema_hall.capacity", read_only=True)

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "tickets_available",
            "taken_places"
        )

    def get_tickets_available(self, obj):
        total_seats = obj.cinema_hall.rows * obj.cinema_hall.seats_in_row
        taken = obj.tickets.count()
        return total_seats - taken

    def get_taken_places(self, obj):
        tickets = obj.tickets.all()
        return [{"row": ticket.row, "seat": ticket.seat} for ticket in tickets]


class MovieSessionDetailSerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(source="cinema_hall.name", read_only=True)
    cinema_hall_capacity = serializers.IntegerField(source="cinema_hall.capacity", read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "taken_places"
        )

    def get_taken_places(self, obj):
        tickets = obj.tickets.all()
        return [{"row": ticket.row, "seat": ticket.seat} for ticket in tickets]


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionDetailSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")