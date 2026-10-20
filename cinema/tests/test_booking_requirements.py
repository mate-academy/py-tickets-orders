from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from cinema.models import Actor, CinemaHall, Genre, Movie, MovieSession
from cinema.models import Order, Ticket
from user.models import User


class BookingRequirementsTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(username="customer")
        self.other_user = User.objects.create_user(username="other")
        self.client.force_authenticate(self.user)
        self.movie = Movie.objects.create(
            title="First Movie", description="Description", duration=90
        )
        self.hall = CinemaHall.objects.create(
            name="Blue", rows=2, seats_in_row=3
        )
        self.session = MovieSession.objects.create(
            movie=self.movie, cinema_hall=self.hall, show_time=timezone.now()
        )
        self.ticket = {
            "movie_session": self.session.pk, "row": 1, "seat": 1
        }
        self.url = "/api/cinema/orders/"

    def test_anonymous_orders_are_denied(self) -> None:
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        response = self.client.post(
            self.url, {"tickets": [self.ticket]}, format="json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Order.objects.exists())

    def test_nested_order_creation_uses_authenticated_user(self) -> None:
        response = self.client.post(
            self.url,
            {
                "user": self.other_user.pk,
                "tickets": [self.ticket, {**self.ticket, "seat": 2}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        order = Order.objects.get()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.tickets.count(), 2)
        response = self.client.get(self.url)
        session = response.data["results"][0]["tickets"][0]["movie_session"]
        self.assertEqual(session["movie_title"], self.movie.title)

    def test_orders_are_private_and_paginated(self) -> None:
        Order.objects.create(user=self.other_user)
        for _ in range(11):
            Order.objects.create(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.data["count"], 11)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])
        response = self.client.get(self.url, {"page": 2})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["previous"])
        self.assertIsNone(response.data["next"])

    def test_invalid_tickets_do_not_create_orders(self) -> None:
        for change in (
            {"row": 0}, {"row": 3}, {"seat": 0}, {"seat": 4},
            {"movie_session": self.session.pk + 100},
        ):
            with self.subTest(change=change):
                response = self.client.post(
                    self.url,
                    {"tickets": [self.ticket, {**self.ticket, **change}]},
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertFalse(Order.objects.exists())
                self.assertFalse(Ticket.objects.exists())

    def test_empty_and_duplicate_tickets_are_rejected(self) -> None:
        for tickets in ([], [self.ticket, self.ticket]):
            response = self.client.post(
                self.url, {"tickets": tickets}, format="json"
            )
            self.assertEqual(response.status_code, 400)
            self.assertFalse(Order.objects.exists())

    def test_taken_seat_is_rejected_and_availability_updates(self) -> None:
        response = self.client.post(
            self.url, {"tickets": [self.ticket]}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.post(
            self.url, {"tickets": [self.ticket]}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 1)
        response = self.client.get("/api/cinema/movie_sessions/")
        self.assertEqual(response.data[0]["tickets_available"], 5)
        response = self.client.get(
            f"/api/cinema/movie_sessions/{self.session.pk}/"
        )
        self.assertEqual(response.data["taken_places"], [{"row": 1, "seat": 1}])

    def test_order_rolls_back_if_a_later_ticket_fails_to_save(self) -> None:
        original_save = Ticket.save

        def save_ticket(ticket: Ticket, *args, **kwargs) -> None:
            if ticket.seat == 2:
                raise ValidationError("Seat became unavailable")
            original_save(ticket, *args, **kwargs)

        with patch.object(Ticket, "save", save_ticket):
            response = self.client.post(
                self.url,
                {"tickets": [self.ticket, {**self.ticket, "seat": 2}]},
                format="json",
            )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Ticket.objects.exists())

    def test_combined_movie_filters_remove_duplicates(self) -> None:
        genres = [
            Genre.objects.create(name="Drama"),
            Genre.objects.create(name="Comedy"),
        ]
        actors = [
            Actor.objects.create(first_name="First", last_name="Actor"),
            Actor.objects.create(first_name="Second", last_name="Actor"),
        ]
        self.movie.genres.add(*genres)
        self.movie.actors.add(*actors)
        Movie.objects.create(
            title="Unrelated", description="Description", duration=90
        )
        response = self.client.get(
            "/api/cinema/movies/",
            {
                "genres": ",".join(str(genre.pk) for genre in genres),
                "actors": ",".join(str(actor.pk) for actor in actors),
                "title": "FIRST",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [movie["id"] for movie in response.data], [self.movie.pk]
        )

    def test_malformed_filters_return_bad_request(self) -> None:
        for url in (
            "/api/cinema/movies/?genres=abc",
            "/api/cinema/movies/?actors=1,abc",
            "/api/cinema/movie_sessions/?date=invalid",
            "/api/cinema/movie_sessions/?movie=abc",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 400)
