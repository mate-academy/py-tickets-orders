import datetime
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from cinema.models import Movie, Genre, Actor, MovieSession, CinemaHall

class MovieSessionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.genre = Genre.objects.create(name="Drama")
        self.actor = Actor.objects.create(first_name="Kate", last_name="Winslet")
        self.movie = Movie.objects.create(title="Titanic", description="Desc", duration=123)
        self.hall = CinemaHall.objects.create(name="White", rows=10, seats_in_row=14)
        self.session = MovieSession.objects.create(
            movie=self.movie,
            cinema_hall=self.hall,
            show_time=timezone.make_aware(datetime.datetime(2022, 9, 2, 9, 0))
        )

    def test_get_movie_sessions(self):
        response = self.client.get("/api/cinema/movie_sessions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["movie_title"], "Titanic")

    def test_get_movie_sessions_filtered_by_date(self):
        response = self.client.get("/api/cinema/movie_sessions/?date=2022-09-02")
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_movie_sessions_filtered_by_movie(self):
        response = self.client.get(f"/api/cinema/movie_sessions/?movie={self.movie.id}")
        self.assertEqual(len(response.data["results"]), 1)
