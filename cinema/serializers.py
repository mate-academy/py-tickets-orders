from rest_framework.pagination import PageNumberPagination

from django.db import transaction

from django.core.exceptions import ValidationError as DjangoValidationError

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
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors"
        )


class MovieSessionMovieSerializer(MovieSerializer):
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )

    class Meta:
        model = Movie
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors"
        )


class MovieSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class MovieSessionListSerializer(MovieSessionSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name",
        read_only=True
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity",
        read_only=True
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
            "tickets_available",
        )


class TicketTakenSeatsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = ("row", "seat")


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieSessionMovieSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    taken_places = TicketTakenSeatsSerializer(
        source="tickets",
        many=True,
        read_only=True
    )

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
            "taken_places"
        )


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")

    def validate(self, attrs):
        ticket = Ticket(
            row=attrs["row"],
            seat=attrs["seat"],
            movie_session=attrs["movie_session"]
        )

        try:
            ticket.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        duplicated_seat = Ticket.objects.filter(
            movie_session=attrs["movie_session"],
            row=attrs["row"],
            seat=attrs["seat"]
        ).exists()

        if duplicated_seat:
            raise serializers.ValidationError(
                f"Місце {attrs['seat']} у ряді {attrs['row']} "
                f"вже заброньовано на цей сеанс."
            )

        return attrs


class TicketListSerializer(serializers.ModelSerializer):
    movie_session = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")

    @staticmethod
    def get_movie_session(obj):
        session = obj.movie_session

        s_id = session.id
        s_time = session.show_time.isoformat()
        s_time_formatted = s_time.replace(
            "+00:00", "Z"
        )
        m_title = session.movie.title
        ch_name = session.cinema_hall.name
        ch_cap = session.cinema_hall.capacity

        return {
            "id": s_id,
            "show_time": s_time_formatted,
            "movie_title": m_title,
            "cinema_hall_name": ch_name,
            "cinema_hall_capacity": ch_cap,
        }


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)

            tickets = [
                Ticket(order=order, **ticket_data)
                for ticket_data in tickets_data
            ]
            Ticket.objects.bulk_create(tickets)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
