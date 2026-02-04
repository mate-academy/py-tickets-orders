import datetime

from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from cinema.models import (
    Movie,
    Genre,
    Actor,
    MovieSession,
    CinemaHall,
    Ticket,
    Order,
)
from user.models import User


class MovieSessionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        drama = Genre.objects.create(
            name="Drama",
        )
        comedy = Genre.objects.create(
            name="Comedy",
        )
        actress = Actor.objects.create(first_name="Kate", last_name="Winslet")
        self.movie = Movie.objects.create(
            title="Titanic",
            description="Titanic description",
            duration=123,
        )
        self.movie.genres.add(drama)
        self.movie.genres.add(comedy)
        self.movie.actors.add(actress)
        self.cinema_hall = CinemaHall.objects.create(
            name="White",
            rows=10,
            seats_in_row=14,
        )
        self.movie_session = MovieSession.objects.create(
            movie=self.movie,
            cinema_hall=self.cinema_hall,
            show_time=datetime.datetime(
                year=2022,
                month=9,
                day=2,
                hour=9
            ),
        )

    def test_get_movie_sessions(self):
        movie_sessions = self.client.get("/api/cinema/movie_sessions/")
        movie_session = {
            "movie_title": "Titanic",
            "cinema_hall_name": "White",
            "cinema_hall_capacity": 140,
        }
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        for field in movie_session:
            self.assertEqual(
                movie_sessions.data["results"][0][field], movie_session[field]
            )

    def test_get_movie_sessions_filtered_by_date(self):
        movie_sessions = self.client.get(
            "/api/cinema/movie_sessions/?date=2022-09-02"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data["results"]), 1)

        movie_sessions = self.client.get(
            "/api/cinema/movie_sessions/?date=2022-09-01"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data["results"]), 0)

    def test_get_movie_sessions_filtered_by_movie(self):
        movie_sessions = self.client.get(
            f"/api/cinema/movie_sessions/?movie={self.movie.id}"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data["results"]), 1)

        movie_sessions = self.client.get(
            "/api/cinema/movie_sessions/?movie=1234"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data["results"]), 0)

    def test_get_movie_sessions_filtered_by_movie_and_data(self):
        movie_sessions = self.client.get(
            f"/api/cinema/movie_sessions/?movie={self.movie.id}&date=2022-09-2"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data["results"]), 1)

        movie_sessions = self.client.get(
            "/api/cinema/movie_sessions/?movie=1234&date=2022-09-2"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data["results"]), 0)

        movie_sessions = self.client.get(
            f"/api/cinema/movie_sessions/?movie={self.movie.id}&date=2022-09-3"
        )
        self.assertEqual(movie_sessions.status_code, status.HTTP_200_OK)
        self.assertEqual(len(movie_sessions.data["results"]), 0)

    def test_post_movie_session(self):
        movies = self.client.post(
            "/api/cinema/movie_sessions/",
            {
                "movie": 1,
                "cinema_hall": 1,
                "show_time": datetime.datetime.now(),
            },
        )
        movie_sessions = MovieSession.objects.all()
        self.assertEqual(movies.status_code, status.HTTP_201_CREATED)
        self.assertEqual(movie_sessions.count(), 2)

    def test_get_movie_session(self):
        response = self.client.get("/api/cinema/movie_sessions/1/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["movie"]["title"], "Titanic")
        self.assertEqual(
            response.data["movie"]["description"], "Titanic description"
        )
        self.assertEqual(response.data["movie"]["duration"], 123)
        self.assertEqual(response.data["movie"]["genres"], ["Drama", "Comedy"])
        self.assertEqual(response.data["movie"]["actors"], ["Kate Winslet"])
        self.assertEqual(response.data["cinema_hall"]["capacity"], 140)
        self.assertEqual(response.data["cinema_hall"]["rows"], 10)
        self.assertEqual(response.data["cinema_hall"]["seats_in_row"], 14)
        self.assertEqual(response.data["cinema_hall"]["name"], "White")

    def test_movie_session_list_shows_tickets_available(self):
        """Test that movie session list includes tickets_available field"""
        # Create a user and order with tickets
        user = User.objects.create(username="testuser")
        order = Order.objects.create(user=user)
        
        # Create 3 tickets for the movie session
        Ticket.objects.create(
            movie_session=self.movie_session,
            order=order,
            row=1,
            seat=1
        )
        Ticket.objects.create(
            movie_session=self.movie_session,
            order=order,
            row=1,
            seat=2
        )
        Ticket.objects.create(
            movie_session=self.movie_session,
            order=order,
            row=1,
            seat=3
        )
        
        response = self.client.get("/api/cinema/movie_sessions/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tickets_available", response.data["results"][0])
        
        # Cinema hall capacity (10 * 14 = 140) - 3 tickets sold = 137 available
        expected_available = self.cinema_hall.capacity - 3
        self.assertEqual(
            response.data["results"][0]["tickets_available"],
            expected_available
        )

    def test_movie_session_detail_shows_taken_places(self):
        """Test that movie session detail includes taken_places field"""
        # Create a user and order with tickets
        user = User.objects.create(username="testuser")
        order = Order.objects.create(user=user)
        
        # Create tickets with specific seats
        Ticket.objects.create(
            movie_session=self.movie_session,
            order=order,
            row=5,
            seat=7
        )
        Ticket.objects.create(
            movie_session=self.movie_session,
            order=order,
            row=3,
            seat=9
        )
        
        response = self.client.get(
            f"/api/cinema/movie_sessions/{self.movie_session.id}/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("taken_places", response.data)
        
        taken_places = response.data["taken_places"]
        self.assertEqual(len(taken_places), 2)
        
        # Check that taken places include our tickets
        seats = [(place["row"], place["seat"]) for place in taken_places]
        self.assertIn((5, 7), seats)
        self.assertIn((3, 9), seats)
