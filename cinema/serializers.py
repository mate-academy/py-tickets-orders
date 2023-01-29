from rest_framework import serializers

from cinema.models import (
    Genre, Actor, CinemaHall, Movie, MovieSession, Order, Ticket
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


class TicketSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(many=False, read_only=True)
    cinema_hall = CinemaHallSerializer(many=False, read_only=True)
    taken_places = TicketSeatSerializer(source="tickets", many=True,
                                        read_only=True)

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")


class TicketDetailSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionListSerializer(many=False)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs):
        data = super().validate(attrs)
        ticket_row = attrs["row"]
        ticket_seat = attrs["seat"]
        cinema_hall_rows = attrs["movie_session"].cinema_hall.rows
        cinema_hall_seats = attrs["movie_session"].cinema_hall.seats_in_row

        if not (1 <= ticket_row <= cinema_hall_rows):
            raise serializers.ValidationError({
                "row": f"Row number must be in available range: "
                       f"1..{cinema_hall_rows}"
            })

        if not (1 <= ticket_seat <= cinema_hall_seats):
            raise serializers.ValidationError({
                "row": f"Seat number must be in available range: "
                       f"1..{cinema_hall_seats}"
            })

        return data


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True)

    class Meta:
        model = Order
        fields = ("tickets",)


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketDetailSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")
