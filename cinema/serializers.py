from typing import Type
from rest_framework import serializers
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
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")

    def get_full_name(self, obj: Actor) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()


class CinemaHallSerializer(serializers.ModelSerializer):
    capacity = serializers.SerializerMethodField()

    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")

    def get_capacity(self, obj: CinemaHall) -> int:
        return int(obj.rows * obj.seats_in_row)


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieListSerializer(MovieSerializer):
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    actors = serializers.SerializerMethodField()

    def get_actors(self, obj: Movie) -> list[str]:
        return [
            f"{a.first_name} {a.last_name}".strip() for a in obj.actors.all()
        ]


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


class MovieSessionShortSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity"
        )

    def get_cinema_hall_capacity(self, obj: MovieSession) -> int:
        hall = obj.cinema_hall
        return int(hall.rows * hall.seats_in_row)


class MovieSessionListSerializer(MovieSessionShortSerializer):
    tickets_available = serializers.SerializerMethodField()

    class Meta(MovieSessionShortSerializer.Meta):
        fields = MovieSessionShortSerializer.Meta.fields + (
            "tickets_available",
        )

    def get_tickets_available(self, obj: MovieSession) -> int:
        capacity = self.get_cinema_hall_capacity(obj)
        taken = getattr(obj, "tickets_count", None)
        if taken is None:
            taken = obj.tickets.count()
        left = capacity - int(taken)
        return left if left > 0 else 0


class MovieSessionDetailSerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj: MovieSession) -> list[dict[str, int]]:
        return list(obj.tickets.values("row", "seat"))


class MovieSessionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class TicketInOrderSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionShortSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs: dict) -> dict:
        ms: MovieSession = attrs["movie_session"]
        row: int = attrs["row"]
        seat: int = attrs["seat"]
        hall = ms.cinema_hall
        if row < 1 or row > hall.rows:
            raise serializers.ValidationError({"row": "Invalid row"})
        if seat < 1 or seat > hall.seats_in_row:
            raise serializers.ValidationError({"seat": "Invalid seat"})
        if Ticket.objects.filter(
                movie_session=ms, row=row, seat=seat
        ).exists():
            raise serializers.ValidationError(
                "This seat is already taken for the session"
            )
        return attrs


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketInOrderSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")


class OrderWriteSerializer(serializers.ModelSerializer):
    tickets = TicketWriteSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")
        read_only_fields = ("id", "created_at")

    def validate(self, attrs: dict) -> dict:
        items = self.initial_data.get("tickets", [])
        seen: set[tuple[int, int, int]] = set()
        for it in items:
            ms_id = int(it["movie_session"])
            row = int(it["row"])
            seat = int(it["seat"])
            key = (ms_id, row, seat)
            if key in seen:
                raise serializers.ValidationError(
                    "Duplicate tickets in one order"
                )
            seen.add(key)
        return attrs

    def create(self, validated_data: dict) -> Order:
        tickets_data = validated_data.pop("tickets", [])
        user = self.context["request"].user
        order = Order.objects.create(user=user)
        Ticket.objects.bulk_create(
            [Ticket(order=order, **td) for td in tickets_data]
        )
        return order
