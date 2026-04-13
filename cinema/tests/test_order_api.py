from datetime import datetime

from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from cinema.models import (
    Movie,
    Genre,
    Actor,
    CinemaHall,
    MovieSession,
    Ticket,
    Order,
)
from user.models import User


class OrderApiTests(TestCase):
    from django.test import TestCase
    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient
    from rest_framework import status
    from cinema.models import Movie, MovieSession, CinemaHall, Order, Ticket

    User = get_user_model()

    class OrderApiTests(TestCase):
        def setUp(self):
            self.client = APIClient()
            self.user = User.objects.create_user(username="testuser", password="password")
            self.client.force_authenticate(user=self.user)
            self.movie = Movie.objects.create(title="Titanic", duration=123)
            self.hall = CinemaHall.objects.create(name="Main", rows=10, seats_in_row=10)
            self.session = MovieSession.objects.create(
                movie=self.movie, cinema_hall=self.hall, show_time="2026-01-01T10:00:00Z"
            )
            self.order = Order.objects.create(user=self.user)
            self.ticket = Ticket.objects.create(movie_session=self.session, row=1, seat=1, order=self.order)

        def test_get_order(self):
            response = self.client.get("/api/cinema/orders/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["count"], 1)
            self.assertEqual(len(response.data["results"][0]["tickets"]), 1)

        def test_movie_session_list_tickets_available(self):
            response = self.client.get("/api/cinema/movie_sessions/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["results"][0]["tickets_available"], 99)
