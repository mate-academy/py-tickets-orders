from rest_framework import serializers
from cinema.models import (CinemaHall,
                           Genre,
                           Actor,
                           Movie,
                           MovieSession,
                           Order,
                           Ticket
                           )


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class MovieSerializer(serializers.ModelSerializer):
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
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors",
        )

    def validate_duration(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Duration must be greater than zero."
            )
        return value


class CinemaHallSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = CinemaHall
        fields = ("id",
                  "name",
                  "rows",
                  "seats_in_row",
                  "capacity"
                  )


class MovieSessionListSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)

    cinema_hall_name = serializers.CharField(source="cinema_hall.name",
                                             read_only=True
                                             )

    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity",
        read_only=True
    )

    tickets_available = serializers.SerializerMethodField()

    class Meta:
        model = MovieSession
        fields = ("id",
                  "show_time",
                  "movie_title",
                  "cinema_hall_name",
                  "cinema_hall_capacity",
                  "tickets_available"
                  )

    def get_tickets_available(self, obj):
        taken_tickets = obj.tickets.count()
        return obj.cinema_hall.capacity - taken_tickets


class TakenPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(
        many=True,
        read_only=True,
    )
    actors = ActorSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Movie
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors",
        )


class MovieSessionMovieDetailSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )
    actors = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name",
    )

    class Meta:
        model = Movie
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "genres",
            "actors",
        )


class MovieSessionDetailSerializer(serializers.ModelSerializer):
    movie = MovieSessionMovieDetailSerializer(read_only=True)

    cinema_hall = CinemaHallSerializer(read_only=True)

    taken_places = TakenPlaceSerializer(source="tickets",
                                        many=True,
                                        read_only=True
                                        )

    class Meta:
        model = MovieSession
        fields = ("id", "show_time", "movie", "cinema_hall", "taken_places")


class TicketMovieSessionSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)

    cinema_hall_name = serializers.CharField(source="cinema_hall.name",
                                             read_only=True
                                             )

    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity",
        read_only=True
    )

    class Meta:
        model = MovieSession
        fields = ("id",
                  "show_time",
                  "movie_title",
                  "cinema_hall_name",
                  "cinema_hall_capacity"
                  )


class TicketSerializer(serializers.ModelSerializer):
    movie_session = serializers.PrimaryKeyRelatedField(
        queryset=MovieSession.objects.all())

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")
        read_only_fields = ("id",)

    def validate(self, attrs):
        movie_session = attrs.get("movie_session",
                                  getattr(self.instance, "movie_session", None)
                                  )

        row = attrs.get("row", getattr(self.instance, "row", None))

        seat = attrs.get("seat", getattr(self.instance, "seat", None))

        if movie_session is None:
            raise serializers.ValidationError(
                {"movie_session": "This field is required."}
            )

        hall = movie_session.cinema_hall

        if row is None or not (1 <= row <= hall.rows):
            raise serializers.ValidationError({"row": "Invalid row number."})

        if seat is None or not (1 <= seat <= hall.seats_in_row):
            raise serializers.ValidationError({"seat": "Invalid seat number."})

        existing_tickets = Ticket.objects.filter(movie_session=movie_session,
                                                 row=row,
                                                 seat=seat
                                                 )

        if self.instance:
            existing_tickets = existing_tickets.exclude(pk=self.instance.pk)

        if existing_tickets.exists():
            raise serializers.ValidationError("This seat is already reserved.")

        return attrs


class OrderTicketSerializer(serializers.ModelSerializer):
    movie_session = TicketMovieSessionSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "movie_session")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, write_only=True)

    tickets_detail = OrderTicketSerializer(source="tickets",
                                           many=True,
                                           read_only=True
                                           )

    class Meta:
        model = Order
        fields = ("id", "tickets", "tickets_detail", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_tickets(self, tickets):
        if not tickets:
            raise serializers.ValidationError(
                "At least one ticket is required."
            )

        reserved_places = set()

        for ticket in tickets:
            place = (ticket["movie_session"].id,
                     ticket["row"],
                     ticket["seat"]
                     )

            if place in reserved_places:
                raise serializers.ValidationError(
                    "Duplicate seats in the same order."
                )

            reserved_places.add(place)

        return tickets

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")

        order = Order.objects.create(user=self.context["request"].user,
                                     **validated_data
                                     )

        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)

        return order

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["tickets"] = OrderTicketSerializer(
            instance.tickets.all(),
            many=True,
            context=self.context).data

        representation.pop("tickets_detail", None)

        return representation


class MovieSessionSerializer(serializers.ModelSerializer):
    movie = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all()
    )
    cinema_hall = serializers.PrimaryKeyRelatedField(
        queryset=CinemaHall.objects.all()
    )

    class Meta:
        model = MovieSession
        fields = (
            "id",
            "show_time",
            "movie",
            "cinema_hall",
        )


class MovieListSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(many=True,
                                          read_only=True,
                                          slug_field="name"
                                          )

    actors = serializers.SlugRelatedField(many=True,
                                          read_only=True,
                                          slug_field="full_name"
                                          )

    class Meta:
        model = Movie
        fields = ("id",
                  "title",
                  "description",
                  "duration",
                  "genres",
                  "actors"
                  )
