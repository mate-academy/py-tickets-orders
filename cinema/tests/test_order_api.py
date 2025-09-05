from datetime import datetime

from django.test import TestCase

from rest_framework.test import APIClient
from django.urls import reverse
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
    def test_create_order(self):
        self.client.login(username=self.user.username, password="adminpass")
        url = reverse("cinema:orders-list")
        payload = {
            "tickets": [
                {
                    "row": 3,
                    "seat": 5,
                    "movie_session": self.movie_session.id
                },
                {
                    "row": 4,
                    "seat": 6,
                    "movie_session": self.movie_session.id
                }
            ]
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.json()["id"]
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.tickets.count(), 2)
        ticket_rows = sorted([t.row for t in order.tickets.all()])
        ticket_seats = sorted([t.seat for t in order.tickets.all()])
        self.assertEqual(ticket_rows, [3, 4])
        self.assertEqual(ticket_seats, [5, 6])
    def setUp(self):
        import uuid
        self.client = APIClient()
        unique_username = f"admin_{uuid.uuid4().hex[:8]}"
        self.user = User.objects.create_user(username=unique_username, password="adminpass")
        self.drama = Genre.objects.create(name="Drama")
        self.comedy = Genre.objects.create(name="Comedy")
        self.actress = Actor.objects.create(first_name="Kate", last_name="Winslet")
        self.movie = Movie.objects.create(title="Titanic", description="Titanic description", duration=123)
        self.movie.genres.add(self.drama)
        self.movie.genres.add(self.comedy)
        self.movie.actors.add(self.actress)
        self.cinema_hall = CinemaHall.objects.create(name="White", rows=10, seats_in_row=14)
        self.movie_session = MovieSession.objects.create(movie=self.movie, cinema_hall=self.cinema_hall, show_time=datetime.now())
        self.order = Order.objects.create(user=self.user)
        self.ticket = Ticket.objects.create(movie_session=self.movie_session, row=2, seat=12, order=self.order)
    def test_get_order(self):
        self.client.login(
            username=self.user.username,
            password="adminpass"
        )
        url = reverse("cinema:orders-list")
        orders_response = self.client.get(url)
        self.assertEqual(orders_response.status_code, status.HTTP_200_OK)
        orders_data = orders_response.json()
        # Defensive: handle both paginated and non-paginated responses
        if "results" in orders_data:
            order = orders_data["results"][0]
        else:
            order = orders_data
        self.assertEqual(len(order["tickets"]), 1)
        ticket = order["tickets"][0]
        self.assertEqual(ticket["row"], 2)
        self.assertEqual(ticket["seat"], 12)
        movie_session = ticket["movie_session"]
        self.assertEqual(movie_session["movie_title"], "Titanic")
        self.assertEqual(movie_session["cinema_hall_name"], "White")
        self.assertEqual(movie_session["cinema_hall_capacity"], 140)

    def test_movie_session_detail_tickets(self):
        url = reverse("cinema:moviesession-detail", args=[self.movie_session.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(
            response_data["taken_places"][0]["row"], self.ticket.row
        )
        self.assertEqual(
            response_data["taken_places"][0]["seat"], self.ticket.seat
        )

    def test_movie_session_list_tickets_available(self):
        url = reverse("cinema:moviesession-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(
            response_data["results"][0]["tickets_available"],
            self.cinema_hall.capacity - 1,
        )
