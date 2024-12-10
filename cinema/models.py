from django.conf import settings
from django.db import models
from rest_framework.exceptions import ValidationError


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
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    cinema_hall = models.ForeignKey(CinemaHall, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-show_time"]

    def __str__(self):
        return self.movie.title + " " + str(self.show_time)


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    def __str__(self):
        return str(self.created_at)

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    movie_session = models.ForeignKey(
        MovieSession,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    order = models.ForeignKey(Order,
                              on_delete=models.CASCADE,
                              related_name="tickets")
    row = models.IntegerField()
    seat = models.IntegerField()

    @staticmethod
    def validate_position(value: int,
                          max_value: int,
                          field_name: str,
                          error_to_raise):
        if not (1 <= value <= max_value):
            raise error_to_raise(
                {field_name: f"{field_name} must be in the range " f"[1, {max_value}]"}
            )

    def clean(self):
        cinema_hall = self.movie_session.cinema_hall
        Ticket.validate_position(self.row,
                                 cinema_hall.rows,
                                 "row",
                                 ValidationError)
        Ticket.validate_position(
            self.seat,
            cinema_hall.seats_in_row,
            "seat",
            ValidationError
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        return f"{self.movie_session} " \
               f"(row: {self.row}," f" seat: {self.seat})"

    class Meta:
        unique_together = ("movie_session", "row", "seat")
