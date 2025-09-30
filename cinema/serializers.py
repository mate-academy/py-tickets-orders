from typing import List
from django.db import IntegrityError, transaction
from rest_framework import serializers


from .models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
    Ticket,
)

# =========================
# ACTOR
# =========================


class ActorListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Actor
        fields = ("id", "full_name")

    def get_full_name(self, obj: Actor) -> str:
        first = (obj.first_name or "").strip()
        last = (obj.last_name or "").strip()
        if first or last:
            return f"{first} {last}".strip()
        return getattr(obj, "full_name", "").strip()


class ActorDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name")


# usado **apenas** dentro do detalhe de Movie (o teste espera `full_name`)
class ActorDetailWithFullNameSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")

    def get_full_name(self, obj: Actor) -> str:
        first = (obj.first_name or "").strip()
        last = (obj.last_name or "").strip()
        if first or last:
            return f"{first} {last}".strip()
        return getattr(obj, "full_name", "").strip()


# =========================
# GENRE
# =========================

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


# =========================
# CINEMA HALL
# =========================

class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHall
        fields = ("id", "name", "rows", "seats_in_row")


class CinemaHallDetailSerializer(CinemaHallSerializer):
    capacity = serializers.SerializerMethodField()

    class Meta(CinemaHallSerializer.Meta):
        fields = CinemaHallSerializer.Meta.fields + ("capacity",)

    def get_capacity(self, obj: CinemaHall) -> int:
        return int(obj.rows) * int(obj.seats_in_row)


# =========================
# MOVIE
# =========================

class MovieListSerializer(serializers.ModelSerializer):
    genres = serializers.SerializerMethodField()
    actors = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")

    def get_genres(self, obj: Movie) -> List[str]:
        return list(obj.genres.all().order_by("id").values_list("name", flat=True))

    def get_actors(self, obj: Movie) -> List[str]:
        names: List[str] = []
        for actor in obj.actors.all().order_by("id"):
            first = (actor.first_name or "").strip()
            last = (actor.last_name or "").strip()
            full = (
                f"{first} {last}".strip()
                or getattr(actor, "full_name", "").strip()
            )
            names.append(full)
        return names


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    # aqui o teste quer também `full_name`
    actors = ActorDetailWithFullNameSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")


class MovieCreateUpdateSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Genre.objects.all(), write_only=True
    )
    actors = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Actor.objects.all(), write_only=True
    )

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")

    def validate_duration(self, value: int) -> int:
        if value is None or value <= 0:
            raise serializers.ValidationError("duration must be a positive integer")
        return value

    def create(self, validated_data):
        genres = validated_data.pop("genres", [])
        actors = validated_data.pop("actors", [])
        movie = Movie.objects.create(**validated_data)
        if genres:
            movie.genres.set(genres)
        if actors:
            movie.actors.set(actors)
        return movie

    def update(self, instance, validated_data):
        genres = validated_data.pop("genres", None)
        actors = validated_data.pop("actors", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if genres is not None:
            instance.genres.set(genres)
        if actors is not None:
            instance.actors.set(actors)
        return instance


class MovieMiniDetailSerializer(serializers.ModelSerializer):
    genres = serializers.SerializerMethodField()
    actors = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ("id", "title", "description", "duration", "genres", "actors")

    def get_genres(self, obj: Movie) -> List[str]:
        return list(obj.genres.all().order_by("id").values_list("name", flat=True))

    def get_actors(self, obj: Movie) -> List[str]:
        names: List[str] = []
        for actor in obj.actors.all().order_by("id"):
            first = (actor.first_name or "").strip()
            last = (actor.last_name or "").strip()
            full = (
                f"{first} {last}".strip()
                or getattr(actor, "full_name", "").strip()
            )
            names.append(full)
        return names


# =========================
# MOVIE SESSION
# =========================

class MovieSessionListSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(source="cinema_hall.name", read_only=True)
    cinema_hall_capacity = serializers.SerializerMethodField()
    tickets_available = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "movie_title",
            "cinema_hall_name",
            "cinema_hall_capacity",
            "show_time",
            "tickets_available",
        )

    def get_cinema_hall_capacity(self, obj: MovieSession) -> int:
        return int(obj.cinema_hall.rows) * int(obj.cinema_hall.seats_in_row)

    def get_tickets_available(self, obj: MovieSession) -> int:
        capacity = self.get_cinema_hall_capacity(obj)
        tickets_qs = obj.tickets if hasattr(obj, "tickets") else obj.ticket_set
        taken = tickets_qs.count()
        return capacity - taken


class MovieSessionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieSession
        fields = ("id", "movie", "cinema_hall", "show_time")


class TakenPlaceSerializer(serializers.Serializer):
    row = serializers.IntegerField()
    seat = serializers.IntegerField()


class MovieSessionDetailSerializer(serializers.ModelSerializer):
    movie = MovieMiniDetailSerializer(read_only=True)
    cinema_hall = CinemaHallDetailSerializer(read_only=True)
    tickets_available = serializers.SerializerMethodField()
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "movie",
            "cinema_hall",
            "show_time",
            "tickets_available",
            "taken_places",
        )

    def get_tickets_available(self, obj: MovieSession) -> int:
        capacity = int(obj.cinema_hall.rows) * int(obj.cinema_hall.seats_in_row)
        tickets_qs = obj.tickets if hasattr(obj, "tickets") else obj.ticket_set
        taken = tickets_qs.count()
        return capacity - taken

    def get_taken_places(self, obj: MovieSession) -> List[dict]:
        qs = obj.tickets.all() if hasattr(obj, "tickets") else obj.ticket_set.all()
        return [{"row": t.row, "seat": t.seat} for t in qs.order_by("row", "seat")]


# =========================
# TICKET / ORDER
# =========================

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "movie_session", "row", "seat")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        ms: MovieSession = instance.movie_session
        hall: CinemaHall = ms.cinema_hall
        capacity = int(hall.rows) * int(hall.seats_in_row)
        data["movie_session"] = {
            "id": ms.id,
            "movie_title": ms.movie.title,
            "cinema_hall_name": hall.name,
            "cinema_hall_capacity": capacity,
            "show_time": ms.show_time.isoformat(),
        }
        return data


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")

    def to_representation(self, instance):
        instance.tickets_list = instance.tickets.all().order_by("id")
        return super().to_representation(instance)


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets")
        read_only_fields = ("id",)

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets", [])
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError(
                {"detail": "Authentication required to create orders."}
            )

        try:
            with transaction.atomic():
                order = Order.objects.create(user=user)
                for ticket in tickets_data:
                    Ticket.objects.create(order=order, **ticket)
        except IntegrityError:
            raise serializers.ValidationError(
                {
                    "tickets": [
                        "Seat already taken for this movie session or invalid."
                    ]
                }
            )
        return order

    def to_representation(self, instance):
        # Reaproveita o serializer de leitura para a resposta do POST
        return OrderSerializer(instance, context=self.context).data
