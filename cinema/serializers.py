from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from cinema.models import (
    Genre, Actor, CinemaHall,
    Movie, MovieSession, Order, Ticket
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
        many=True,
        read_only=True,
        slug_field="name"
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


class MovieSessionListSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name",
        read_only=True
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
        total_capacity = obj.cinema_hall.capacity
        tickets_sold = Ticket.objects.filter(movie_session=obj).count()
        return total_capacity - tickets_sold


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj):
        """
        Retrieve all taken places (row and seat) for the movie session.
        """
        tickets = Ticket.objects.filter(movie_session=obj)
        return [{"row": ticket.row, "seat": ticket.seat} for ticket in tickets]


class TicketSerializer(serializers.ModelSerializer):
    movie_session = serializers.PrimaryKeyRelatedField(
        queryset=MovieSession.objects.all()
    )

    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "movie_session",
        )

    def validate(self, data):
        """
        Validate ticket creation.
        """
        movie_session = data.get("movie_session")
        row = data.get("row")
        seat = data.get("seat")

        # Ensure row and seat are within the cinema hall's capacity
        cinema_hall = movie_session.cinema_hall
        if row < 1 or row > cinema_hall.rows:
            raise ValidationError(
                {
                    "row": (
                        f"Row {row} is out of range (1 to {cinema_hall.rows})."
                    )
                }
            )
        if seat < 1 or seat > cinema_hall.seats_in_row:
            raise ValidationError(
                {
                    "seat": (
                        f"Seat {seat} is out of range (1 to "
                        f"{cinema_hall.seats_in_row})."
                    )
                }
            )

        # Ensure row and seat are not already taken for this movie session
        if Ticket.objects.filter(
                movie_session=movie_session, row=row, seat=seat
        ).exists():
            raise ValidationError(
                {
                    "seat": (
                        f"Row {row}, Seat {seat} is already taken "
                        f"for this session."
                    )
                }
            )

        return data


class TicketMovieListSerializer(TicketSerializer):
    movie_session = MovieSessionListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "movie_session",
        )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = (
            "id",
            "tickets",
            "created_at",
        )

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        user = self.context["request"].user

        with transaction.atomic():
            # Create the order
            order = Order.objects.create(user=user)

            for ticket_data in tickets_data:
                # No need to fetch `movie_session` as it is already validated
                Ticket.objects.create(order=order, **ticket_data)

            return order


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketMovieListSerializer(
        many=True,
        read_only=False,
        allow_empty=False
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "tickets",
            "created_at",
        )
