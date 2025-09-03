from rest_framework import serializers

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Ticket,
    Order,
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
    cinema_hall_capacity = serializers.SerializerMethodField()
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

    def get_cinema_hall_capacity(self, obj: MovieSession) -> int:
        hall = obj.cinema_hall
        cap = getattr(hall, "capacity", None)
        return cap if isinstance(cap, int) else hall.rows * hall.seats_in_row

    def get_tickets_available(self, obj: MovieSession) -> int:
        return self.get_cinema_hall_capacity(obj) - obj.tickets.count()


class MovieSessionDetailSerializer(MovieSessionSerializer):
    movie = MovieListSerializer(read_only=True)
    cinema_hall = CinemaHallSerializer(read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")

    def get_taken_places(self, obj: MovieSession):
        return list(obj.tickets.values("row", "seat"))


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
            "cinema_hall_capacity",
        )

    def get_cinema_hall_capacity(self, obj: MovieSession) -> int:
        hall = obj.cinema_hall
        cap = getattr(hall, "capacity", None)
        return cap if isinstance(cap, int) else hall.rows * hall.seats_in_row


class TicketReadSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionShortSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")
        read_only_fields = fields


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "movie_session")

    def validate(self, attrs):
        ms: MovieSession = attrs["movie_session"]
        row: int = attrs["row"]
        seat: int = attrs["seat"]

        hall = ms.cinema_hall
        if not (1 <= row <= hall.rows):
            raise serializers.ValidationError(
                {"row": f"Row must be in [1..{hall.rows}]"}
            )
        if not (1 <= seat <= hall.seats_in_row):
            raise serializers.ValidationError(
                {"seat": f"Seat must be in [1..{hall.seats_in_row}]"}
            )

        if Ticket.objects.filter(
                movie_session=ms,
                row=row,
                seat=seat
        ).exists():
            raise serializers.ValidationError(
                "This place is already taken for the session"
            )

        return attrs


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketReadSerializer(many=True, source="tickets", read_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def get_tickets(self, obj: Order):
        rel = getattr(obj, "tickets", None) or getattr(obj, "ticket_set", None)
        qs = rel.all() if hasattr(rel, "all") else []
        return TicketReadSerializer(qs, many=True).data


class OrderCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        seen = set()
        for tt in attrs.get("tickets", []):
            key = (tt["movie_session"].id, tt["row"], tt["seat"])
            if key in seen:
                raise serializers.ValidationError(
                    "Duplicate tickets for the same place in request"
                )
            seen.add(key)
        return attrs

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets", [])
        order = Order.objects.create(**validated_data)
        for tt in tickets_data:
            Ticket.objects.create(order=order, **tt)
        return order

    def to_representation(self, instance):
        data = super().to_representation(instance)
        rel = (getattr(instance, "tickets", None)
               or getattr(instance, "ticket_set", None))
        qs = rel.all() if hasattr(rel, "all") else []
        data["tickets"] = TicketReadSerializer(qs, many=True).data
        return data
