from datetime import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from cinema.models import Movie, Genre, Actor, CinemaHall, MovieSession, Ticket, Order
from user.models import User

class OrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username="admin")
        self.client.force_authenticate(user=self.user)
        drama = Genre.objects.create(name="Drama")
        comedy = Genre.objects.create(name="Comedy")
        actress = Actor.objects.create(first_name="Kate", last_name="Winslet")
        self.movie = Movie.objects.create(title="Titanic", description="Titanic description", duration=123)
        self.movie.genres.add(drama, comedy)
        self.movie.actors.add(actress)
        self.cinema_hall = CinemaHall.objects.create(name="White", rows=10, seats_in_row=14)
        self.movie_session = MovieSession.objects.create(movie=self.movie, cinema_hall=self.cinema_hall, show_time=datetime.now())
        self.order = Order.objects.create(user=self.user)
        self.ticket = Ticket.objects.create(movie_session=self.movie_session, row=2, seat=12, order=self.order)

    def test_get_order(self):
        response = self.client.get("/api/cinema/orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["tickets"][0]["row"], 2)
        self.assertEqual(response.data[0]["tickets"][0]["seat"], 12)

    def test_movie_session_detail_tickets(self):
        response = self.client.get(f"/api/cinema/movie_sessions/{self.movie_session.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["taken_places"][0]["row"], self.ticket.row)
        self.assertEqual(response.data["taken_places"][0]["seat"], self.ticket.seat)

    def test_movie_session_list_tickets_available(self):
        response = self.client.get("/api/cinema/movie_sessions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["tickets_available"], self.cinema_hall.capacity - 1)
