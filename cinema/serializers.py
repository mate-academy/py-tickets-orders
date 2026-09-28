from django.db.models import Count
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


class MovieSessionTicketSerializer(serializers.ModelSerializer):
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


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionTicketSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs):
        movie_session = attrs["movie_session"]
        row = attrs["row"]
        seat = attrs["seat"]
        cinema_hall = movie_session.cinema_hall

        if not (1 <= row <= cinema_hall.rows):
            raise serializers.ValidationError(
                {
                    "row": (
                        f"row number must be in available range: "
                        f"(1, {cinema_hall.rows})"
                    )
                }
            )

        if not (1 <= seat <= cinema_hall.seats_in_row):
            raise serializers.ValidationError(
                {
                    "seat": (
                        f"seat number must be in available range: "
                        f"(1, {cinema_hall.seats_in_row})"
                    )
                }
            )

        if Ticket.objects.filter(
            movie_session=movie_session, row=row, seat=seat
        ).exists():
            raise serializers.ValidationError(
                "This seat is already taken for this movie session."
            )

        return attrs


class MovieSessionListSerializer(MovieSessionSerializer):
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

    def get_tickets_available(self, obj):
        return obj.cinema_hall.capacity - obj.tickets.count()


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
            "taken_places",
        )

    def get_taken_places(self, obj):
        return list(
            obj.tickets.values("row", "seat").order_by("row", "seat")
        )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")
        read_only_fields = ("id", "created_at")

    def validate_tickets(self, value):
        if not value:
            raise serializers.ValidationError(
                "Order must include at least one ticket."
            )
        return value

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        user = self.context["request"].user
        order = Order.objects.create(user=user)

        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)

        return order


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")
