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
    def setUp(self) -> None:
        self.client = APIClient()
        self.drama = Genre.objects.create(name="Drama")
        self.comedy = Genre.objects.create(name="Comedy")
        self.actress = Actor.objects.create(first_name="Kate", last_name="Winslet")

        self.movie = Movie.objects.create(
            title="Titanic",
            description="Titanic description",
            duration=123,
        )
        self.movie.genres.add(self.drama)
        self.movie.genres.add(self.comedy)
        self.movie.actors.add(self.actress)

        self.cinema_hall = CinemaHall.objects.create(
            name="White",
            rows=10,
            seats_in_row=14,
        )

        self.movie_session = MovieSession.objects.create(
            movie=self.movie,
            cinema_hall=self.cinema_hall,
            show_time=datetime(
                year=2022,
                month=9,
                day=2,
                hour=9
            ),
        )

        self.user = User.objects.create(username="admin")
        self.client.force_authenticate(user=self.user)

        self.order = Order.objects.create(user=self.user)
        self.ticket = Ticket.objects.create(
            movie_session=self.movie_session, row=2, seat=12, order=self.order
        )

    def test_get_order(self) -> None:
        orders_response = self.client.get("/api/cinema/orders/")

        self.assertEqual(orders_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(orders_response.data["results"]), 1)

        order = orders_response.data["results"][0]
        self.assertEqual(len(order["tickets"]), 1)

        ticket = order["tickets"][0]
        self.assertEqual(ticket["row"], 2)
        self.assertEqual(ticket["seat"], 12)

        movie_session = ticket["movie_session"]
        self.assertEqual(movie_session["movie_title"], "Titanic")
        self.assertEqual(movie_session["cinema_hall_name"], "White")
        self.assertEqual(movie_session["cinema_hall_capacity"], 140)

    def test_movie_session_detail_tickets(self) -> None:
        response = self.client.get(
            f"/api/cinema/movie_sessions/{self.movie_session.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        taken_places = response.data["taken_places"]
        self.assertEqual(len(taken_places), 1)
        self.assertEqual(taken_places[0]["row"], self.ticket.row)
        self.assertEqual(taken_places[0]["seat"], self.ticket.seat)

    def test_movie_session_list_tickets_available(self) -> None:
        response = self.client.get("/api/cinema/movie_sessions/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0]["tickets_available"],
            self.cinema_hall.capacity - 1,
        )

    def test_post_order_with_tickets(self) -> None:
        initial_order_count = Order.objects.count()
        initial_ticket_count = Ticket.objects.count()

        payload = {
            "tickets": [
                {"movie_session": self.movie_session.id, "row": 5, "seat": 5},
                {"movie_session": self.movie_session.id, "row": 5, "seat": 6},
            ]
        }

        response = self.client.post("/api/cinema/orders/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), initial_order_count + 1)
        self.assertEqual(Ticket.objects.count(), initial_ticket_count + 2)

        new_order = Order.objects.get(id=response.data["id"])
        self.assertEqual(new_order.tickets.count(), 2)
