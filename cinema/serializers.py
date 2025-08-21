from rest_framework import serializers as sz
from .models import (
    Movie, Genre, Actor, CinemaHall as CH,
    MovieSession as MS, Ticket, Order
)


# ---- Movie ----
class MovieListSerializer(sz.ModelSerializer):
    genres = sz.SlugRelatedField(
        slug_field="name", many=True, read_only=True
    )
    actors = sz.SlugRelatedField(
        slug_field="full_name", many=True, read_only=True
    )

    class Meta:
        model = Movie
        fields = (
            "id", "title", "description", "duration",
            "genres", "actors"
        )


# ---- MS list ----
class MovieSessionListSerializer(sz.ModelSerializer):
    movie_title = sz.CharField(
        source="movie.title", read_only=True
    )
    cinema_hall_name = sz.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = sz.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
    tickets_available = sz.SerializerMethodField()

    class Meta:
        model = MS
        fields = (
            "id", "show_time", "movie_title",
            "cinema_hall_name", "cinema_hall_capacity",
            "tickets_available",
        )

    def get_tickets_available(self, obj) -> int:
        taken = Ticket.objects.filter(movie_session=obj).count()
        return obj.cinema_hall.capacity - taken


# ---- nested Movie for MS detail ----
class MovieNestedSerializer(sz.ModelSerializer):
    genres = sz.SlugRelatedField(
        slug_field="name", many=True, read_only=True
    )
    actors = sz.SlugRelatedField(
        slug_field="full_name", many=True, read_only=True
    )

    class Meta:
        model = Movie
        fields = (
            "id", "title", "description", "duration",
            "genres", "actors"
        )


class CinemaHallSerializer(sz.ModelSerializer):
    capacity = sz.IntegerField(read_only=True)

    class Meta:
        model = CH
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieSessionDetailSerializer(sz.ModelSerializer):
    movie = MovieNestedSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    taken_places = sz.SerializerMethodField()

    class Meta:
        model = MS
        fields = ("id", "show_time", "movie",
                  "cinema_hall", "taken_places")

    def get_taken_places(self, obj):
        qs = (
            Ticket.objects
            .filter(movie_session=obj)
            .values("row", "seat")
            .order_by("row", "seat")
        )
        return list(qs)


# ---- Ticket in Order ----
class TicketCreateSerializer(sz.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs):
        ms = attrs["movie_session"]
        row = attrs["row"]
        seat = attrs["seat"]
        if not (1 <= row <= ms.cinema_hall.rows):
            raise sz.ValidationError(
                {"row": "Row out of range for this hall."}
            )
        if not (1 <= seat <= ms.cinema_hall.seats_in_row):
            raise sz.ValidationError(
                {"seat": "Seat out of range for this hall."}
            )
        exists = Ticket.objects.filter(
            movie_session=ms, row=row, seat=seat
        ).exists()
        if exists:
            raise sz.ValidationError(
                "This place is already taken for the session."
            )
        return attrs


class MovieSessionShortSerializer(sz.ModelSerializer):
    movie_title = sz.CharField(
        source="movie.title", read_only=True
    )
    cinema_hall_name = sz.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = sz.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )

    class Meta:
        model = MS
        fields = (
            "id", "show_time", "movie_title",
            "cinema_hall_name", "cinema_hall_capacity"
        )


class TicketReadSerializer(sz.ModelSerializer):
    movie_session = MovieSessionShortSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class OrderListCreateSerializer(sz.ModelSerializer):
    tickets = TicketReadSerializer(many=True, read_only=True)
    created_at = sz.DateTimeField(read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")


class OrderCreateSerializer(sz.ModelSerializer):
    tickets = TicketCreateSerializer(
        many=True, write_only=True
    )

    class Meta:
        model = Order
        fields = ("id", "tickets")

    def create(self, validated_data):
        t_data = validated_data.pop("tickets", [])
        user = self.context["request"].user
        order = Order.objects.create(user=user)
        for t in t_data:
            Ticket.objects.create(order=order, **t)
        return order
