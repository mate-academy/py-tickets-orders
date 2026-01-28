from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import QuerySet
from rest_framework import serializers

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
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
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")

    def get_full_name(self, obj: Actor) -> str:
        first = (obj.first_name or "").strip()
        last = (obj.last_name or "").strip()
        return f"{first} {last}".strip()


class CinemaHallSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class MovieListSerializer(serializers.ModelSerializer):
    genres = serializers.SerializerMethodField()
    actors = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")

    def get_genres(self, obj: Movie) -> list[str]:
        qs: QuerySet[Genre] = obj.genres.all()
        return [genre.name for genre in qs]

    def get_actors(self, obj: Movie) -> list[str]:
        qs: QuerySet[Actor] = obj.actors.all()
        result: list[str] = []
        for actor in qs:
            first = (actor.first_name or "").strip()
            last = (actor.last_name or "").strip()
            result.append(f"{first} {last}".strip())
        return result


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieWriteSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
    )
    actors = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Actor.objects.all(),
    )

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieSessionListSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name",
        read_only=True,
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity",
        read_only=True,
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


class TakenPlaceSerializer(serializers.Serializer):
    row = serializers.IntegerField()
    seat = serializers.IntegerField()


class MovieSessionDetailSerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
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

    def get_taken_places(self, obj: MovieSession) -> list[dict[str, int]]:
        places = (
            Ticket.objects.filter(movie_session=obj)
            .values("row", "seat")
            .order_by("row", "seat")
        )
        return list(places)


class MovieSessionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall")


class TicketMovieSessionShortSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name",
        read_only=True,
    )
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity",
        read_only=True,
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


class TicketListSerializer(serializers.ModelSerializer):
    movie_session = TicketMovieSessionShortSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        row = attrs.get("row")
        seat = attrs.get("seat")
        movie_session: MovieSession = attrs.get("movie_session")

        cinema_hall = movie_session.cinema_hall
        if row < 1 or row > cinema_hall.rows:
            raise serializers.ValidationError(
                {"row": "Row number is out of range."}
            )
        if seat < 1 or seat > cinema_hall.seats_in_row:
            raise serializers.ValidationError(
                {"seat": "Seat number is out of range."}
            )

        is_taken = Ticket.objects.filter(
            movie_session=movie_session,
            row=row,
            seat=seat,
        ).exists()
        if is_taken:
            raise serializers.ValidationError("This place is already taken.")

        return attrs


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_tickets(
        self,
        tickets: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        seen: set[tuple[int, int, int]] = set()
        for item in tickets:
            ms = item["movie_session"]
            key = (ms.id, item["row"], item["seat"])
            if key in seen:
                raise serializers.ValidationError(
                    "Duplicate tickets in request."
                )
            seen.add(key)
        return tickets

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> Order:
        tickets_data = validated_data.pop("tickets", [])
        request = self.context.get("request")
        user = getattr(request, "user", None)

        order = Order.objects.create(user=user)

        tickets_to_create: list[Ticket] = []
        for ticket in tickets_data:
            tickets_to_create.append(Ticket(order=order, **ticket))

        Ticket.objects.bulk_create(tickets_to_create)
        return order
