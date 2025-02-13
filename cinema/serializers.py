from typing import Any

from rest_framework import serializers

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Ticket,
    Order
)


class CustomListSerializer(serializers.ListSerializer):
    def __getattr__(self, key: str) -> Any:
        if hasattr(self, "child") and self.child is not None:
            if hasattr(self.child, key):
                return getattr(self.child, key)
            else:
                raise AttributeError(
                    f"'{type(self.child).__name__}' "
                    f"object has no attribute '{key}'"
                )
        else:
            raise AttributeError(
                f"'{type(self).__name__}'"
                f" object has no attribute 'child' or 'child' is None"
            )


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieSerializer(serializers.ModelSerializer):
    actors = ActorSerializer(many=True)

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
    list_serializer_class = CustomListSerializer
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
            "tickets_available"
        )

    def get_tickets_available(self, instance: MovieSession) -> int:
        total = instance.cinema_hall.capacity
        taken = instance.tickets.count()
        return total - taken


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, instance: MovieSession) -> list:
        return [
            {"row": ticket.row, "seat": ticket.seat}
            for ticket in instance.tickets.all()
        ]


class TicketOrderReadSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketOrderWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")


class OrderReadSerializer(serializers.ModelSerializer):
    tickets = TicketOrderReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")


class OrderWriteSerializer(serializers.ModelSerializer):
    tickets = TicketOrderWriteSerializer(many=True)

    class Meta:
        model = Order
        fields = ("tickets",)

    def create(self, validated_data: dict) -> Order:
        tickets_data = validated_data.pop("tickets")
        user = self.context["request"].user
        order = Order.objects.create(user=user)
        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)
        return order
