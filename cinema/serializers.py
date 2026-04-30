from django.db import transaction
from rest_framework import serializers

from cinema.models import (
    Genre,
    Actor,
    Movie,
    CinemaHall,
    MovieSession,
    Ticket,
    Order
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")
        # Поле full_name подтянется из @property модели Actor
        read_only_fields = ("full_name",)


class MovieSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True, slug_field="name", read_only=True
    )
    actors = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")

    def get_actors(self, obj):
        return [actor.full_name for actor in obj.actors.all()]


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieCreateSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Genre.objects.all(), required=False
    )
    actors = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Actor.objects.all(), required=False
    )

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class CinemaHallSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieSessionListSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
    # tickets_available = serializers.SerializerMethodField()
    tickets_available = serializers.IntegerField(read_only=True)

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


class MovieSessionMovieSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True, slug_field="name", read_only=True
    )
    actors = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")

    def get_actors(self, obj):
        return [actor.full_name for actor in obj.actors.all()]


class TicketMovieSessionSerializer(serializers.ModelSerializer):
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
            "cinema_hall_capacity"
        )


class TicketPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class TicketSerializer(serializers.ModelSerializer):
    movie_session = TicketMovieSessionSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")

    def validate(self, attrs):
        # Опциональная задача: валидация мест
        data = Ticket.objects.filter(
            movie_session=attrs["movie_session"],
            row=attrs["row"],
            seat=attrs["seat"]
        )
        if data.exists():
            raise serializers.ValidationError("This seat is already taken.")
        return attrs


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")

    def validate(self, attrs):
        movie_session = attrs["movie_session"]
        row = attrs["row"]
        seat = attrs["seat"]
        cinema_hall = movie_session.cinema_hall

        if not (1 <= row <= cinema_hall.rows):
            raise serializers.ValidationError(
                {"row": f"row number must be in range [1, {cinema_hall.rows}]"}
            )
        if not (1 <= seat <= cinema_hall.seats_in_row):
            raise serializers.ValidationError(
                {
                    "seat": (
                        f"seat number must be in range [1, "
                        f"{cinema_hall.seats_in_row}]"
                    )
                }
            )
        if Ticket.objects.filter(
            movie_session=movie_session, row=row, seat=seat
        ).exists():
            raise serializers.ValidationError(
                f"Ticket for row {row}, seat {seat} already exists."
            )
        return attrs


class MovieSessionDetailSerializer(serializers.ModelSerializer):
    movie = MovieSessionMovieSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    # taken_places = serializers.SerializerMethodField()
    taken_places = TicketSerializer(
        source="tickets", many=True, read_only=True
    )

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj):
        return TicketPlaceSerializer(obj.tickets.all(), many=True).data


class MovieSessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        order = Order.objects.create(**validated_data)
        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)
        return order


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order
