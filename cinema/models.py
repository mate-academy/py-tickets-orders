from django.conf import settings
from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self) -> str:
        full = f"{self.first_name} {self.last_name}".strip()
        return full or "Actor"


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # compatível com a migração 0003
    duration = models.PositiveIntegerField(null=True, blank=True)
    genres = models.ManyToManyField(Genre, related_name="movies", blank=True)
    actors = models.ManyToManyField(Actor, related_name="movies", blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class CinemaHall(models.Model):
    name = models.CharField(max_length=255)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def capacity(self) -> int:
        return int(self.rows) * int(self.seats_in_row)


class MovieSession(models.Model):
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="movie_sessions"
    )
    cinema_hall = models.ForeignKey(
        CinemaHall, on_delete=models.CASCADE, related_name="movie_sessions"
    )
    show_time = models.DateTimeField()

    class Meta:
        ordering = ["show_time"]

    def __str__(self) -> str:
        return f"{self.movie} @ {self.cinema_hall} ({self.show_time})"


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order #{self.pk} - {self.user}"


class Ticket(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="tickets"
    )
    movie_session = models.ForeignKey(
        MovieSession, on_delete=models.CASCADE, related_name="tickets"
    )
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()

    class Meta:
        # impede duas vendas para o mesmo assento na mesma sessão
        constraints = [
            models.UniqueConstraint(
                fields=["movie_session", "row", "seat"],
                name="unique_seat_per_session",
            ),
        ]
        indexes = [
            models.Index(fields=["movie_session", "row", "seat"]),
        ]
        ordering = ["movie_session_id", "row", "seat"]

    def __str__(self) -> str:
        return f"{self.movie_session} r{self.row}s{self.seat}"
