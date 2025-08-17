from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueTogetherValidator

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


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField(
        read_only=True,
    )

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj):
        return [
            {"row": ticket.row, "seat": ticket.seat}
            for ticket in obj.tickets.all()
        ]


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(read_only=True,)
    movie_session_id = serializers.PrimaryKeyRelatedField(
        queryset=MovieSession.objects.all(), write_only=True
    )

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session", "movie_session_id")
        validators = [
            UniqueTogetherValidator(
                queryset=Ticket.objects.all(),
                fields=["movie_session", "row", "seat"]
            )
        ]

    def validate(self, attrs):
        for ticket_attr_name, cinema_hall_attr_name in [
            ("row", "rows"),
            ("seat", "seats_in_row"),
        ]:
            ticket_attr_value = attrs.get(ticket_attr_name)
            cinema_hall_count = getattr(
                attrs["movie_session"].cinema_hall, cinema_hall_attr_name
            )
            if not (1 <= ticket_attr_value <= cinema_hall_count):
                raise serializers.ValidationError(
                    {
                        ticket_attr_name:
                            f"{ticket_attr_name}"
                            f" number must be in available range: "
                            f"(1, {cinema_hall_count})"
                    }
                )
        return attrs


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")
