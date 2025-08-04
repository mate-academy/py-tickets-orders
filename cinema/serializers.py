from rest_framework import serializers

from cinema.models import (
    Genre, Actor, CinemaHall,
    Movie, MovieSession, Ticket,
    Order
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

    def get_tickets_available(self, obj):
        total_capacity = obj.cinema_hall.capacity
        taken_tickets_count = obj.tickets.count()
        return total_capacity - taken_tickets_count


class TicketListSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")

    def validate(self, attrs):
        if not (1 <= attrs["row"] <= attrs["movie_session"].cinema_hall.rows):
            raise serializers.ValidationError(
                {"row": "Row number out of range."}
            )
        if not (
                1
                <= attrs["seat"]
                <= attrs["movie_session"].cinema_hall.seats_in_row
        ):
            raise serializers.ValidationError(
                {"seat": "Seat number out of range."}
            )

        if Ticket.objects.filter(
            movie_session=attrs["movie_session"],
            row=attrs["row"],
            seat=attrs["seat"],
        ).exists():
            raise serializers.ValidationError("This seat is already taken.")

        return attrs


class TicketCreateSerializer(serializers.ModelSerializer):
    movie_session = serializers.PrimaryKeyRelatedField(
        queryset=MovieSession.objects.all()
    )

    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs):
        if not (1 <= attrs["row"] <= attrs["movie_session"].cinema_hall.rows):
            raise serializers.ValidationError(
                {"row": "Row number out of range."}
            )
        if not (
                1
                <= attrs["seat"]
                <= attrs["movie_session"].cinema_hall.seats_in_row
        ):
            raise serializers.ValidationError(
                {"seat": "Seat number out of range."}
            )
        if Ticket.objects.filter(
            movie_session=attrs["movie_session"],
            row=attrs["row"],
            seat=attrs["seat"],
        ).exists():
            raise serializers.ValidationError("This seat is already taken.")
        return attrs


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj):
        return obj.tickets.values("row", "seat")


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        user = self.context["request"].user
        order = Order.objects.create(user=user, **validated_data)
        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)
        return order
