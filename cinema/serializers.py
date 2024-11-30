from rest_framework import serializers

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Ticket,
    Order,
)


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
        fields = [
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors",
        ]


class MovieListSerializer(MovieSerializer):
    genres = serializers.SlugRelatedField(
        read_only=True, many=True, slug_field="name"
    )
    actors = serializers.SlugRelatedField(
        read_only=True, many=True, slug_field="full_name"
    )


class MovieDetailSerializer(MovieSerializer):
    genres = GenreSerializer(read_only=True, many=True)
    actors = ActorSerializer(read_only=True, many=True)

    class Meta:
        model = Movie
        fields = ["id", "title", "description", "duration", "genres", "actors"]


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ["id", "show_time", "movie", "cinema_hall"]


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)

    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )

    class Meta:
        model = MovieSession
        fields = [
            "id",
            "show_time",
            "movie_title",
            "tickets_available",
            "cinema_hall_name",
            "cinema_hall_capacity",
        ]


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "movie_session", "row", "seat"]


class TicketListSerializer(TicketSerializer):
    movie_session = MovieSessionListSerializer(read_only=True, many=False)

    class Meta:
        model = Ticket
        fields = ["id", "movie_session", "row", "seat"]


class TicketSeatSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ["row", "seat"]


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(read_only=True, many=False)
    cinema_hall = CinemaHallSerializer(read_only=True, many=False)
    taken_places = TicketSeatSerializer(
        source="tickets", read_only=True, many=True
    )

    class Meta:
        model = MovieSession
        fields = ["id", "show_time", "movie", "cinema_hall", "taken_places"]


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(read_only=False, many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ["tickets"]


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(read_only=True, many=True)

    class Meta:
        model = Order
        fields = ["id", "tickets", "created_at"]
