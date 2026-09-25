"""Regression coverage for order ownership and transactional booking."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from cinema.models import CinemaHall, Movie, MovieSession, Order, Ticket


class OrderValidationTests(APITestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="buyer")
        self.other = get_user_model().objects.create_user(username="other")
        self.client.force_authenticate(self.user)
        movie = Movie.objects.create(
            title="Arrival", description="First contact.", duration=116
        )
        hall = CinemaHall.objects.create(
            name="Blue", rows=3, seats_in_row=4
        )
        self.session = MovieSession.objects.create(
            movie=movie, cinema_hall=hall, show_time=timezone.now()
        )
        self.url = "/api/cinema/orders/"

    def ticket(self, row: int = 1, seat: int = 1) -> dict[str, int]:
        return {
            "row": row, "seat": seat, "movie_session": self.session.pk,
        }

    def test_create_uses_authenticated_owner(self) -> None:
        response = self.client.post(
            self.url,
            {
                "user": self.other.pk,
                "tickets": [self.ticket(), self.ticket(seat=2)],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.get().user_id, self.user.pk)
        self.assertEqual(Ticket.objects.count(), 2)
        sessions = self.client.get("/api/cinema/movie_sessions/")
        self.assertEqual(sessions.data[0]["tickets_available"], 10)

    def test_list_is_private_and_paginated(self) -> None:
        Order.objects.create(user=self.other)
        for _ in range(11):
            Order.objects.create(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 11)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])
        second_page = self.client.get(self.url, {"page": 2})
        self.assertEqual(len(second_page.data["results"]), 1)

    def test_anonymous_requests_are_rejected(self) -> None:
        self.client.force_authenticate(None)
        self.assertIn(self.client.get(self.url).status_code, (401, 403))
        response = self.client.post(
            self.url, {"tickets": [self.ticket()]}, format="json"
        )
        self.assertIn(response.status_code, (401, 403))
        self.assertFalse(Order.objects.exists())

    def test_invalid_seats_do_not_create_orders(self) -> None:
        for row, seat in ((0, 1), (4, 1), (1, 0), (1, 5)):
            with self.subTest(row=row, seat=seat):
                response = self.client.post(
                    self.url,
                    {"tickets": [self.ticket(row, seat)]},
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_duplicate_seats_roll_back_entire_order(self) -> None:
        response = self.client.post(
            self.url,
            {"tickets": [self.ticket(), self.ticket()]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Ticket.objects.exists())

    def test_taken_seat_preserves_existing_booking(self) -> None:
        order = Order.objects.create(user=self.other)
        Ticket.objects.create(
            order=order, movie_session=self.session, row=1, seat=1
        )
        response = self.client.post(
            self.url,
            {"tickets": [self.ticket(seat=2), self.ticket()]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_empty_order_is_rejected(self) -> None:
        response = self.client.post(
            self.url, {"tickets": []}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_malformed_filters_return_client_errors(self) -> None:
        for url in (
            "/api/cinema/movies/?genres=invalid",
            "/api/cinema/movies/?actors=1,",
            "/api/cinema/movie_sessions/?date=2026-02-30",
            "/api/cinema/movie_sessions/?movie=invalid",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 400)
