from django.db import models
from django.conf import settings


class CinemaHall(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return self.first_name + " " + self.last_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.IntegerField()
    genres = models.ManyToManyField(Genre)
    actors = models.ManyToManyField(Actor)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class MovieSession(models.Model):
    show_time = models.DateTimeField()
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="movies"
    )
    cinema_hall = models.ForeignKey(
        CinemaHall, on_delete=models.CASCADE, related_name="cinema_halls"
    )

    class Meta:
        ordering = ["-show_time"]

    def __str__(self):
        return self.movie.title + " " + str(self.show_time)


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="users",
    )

    def __str__(self):
        return str(self.created_at)

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    movie_session = models.ForeignKey(
        MovieSession, on_delete=models.CASCADE, related_name="tickets"
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="tickets"
    )
    row = models.IntegerField()
    seat = models.IntegerField()

    @staticmethod
    def validate_seat(seat: int, seats_in_row: int, error_to_raise):
        if not (1 <= seat <= seats_in_row):
            raise error_to_raise(
                {
                    f"seat number must be"
                    f" in available range 1 to {seats_in_row}"
                }
            )

    def clean(self):
        Ticket.validate_seat(
            self.seat, self.movie_session.cinema_hall.seats_in_row, ValueError
        )

    def __str__(self):
        return (
            f"(row: {self.row}, seat: {self.seat}), {str(self.movie_session)}"
        )

    class Meta:
        unique_together = (
            "row",
            "seat",
            "movie_session",
        )
