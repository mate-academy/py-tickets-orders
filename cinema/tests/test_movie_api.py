from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from cinema.models import Movie, Genre, Actor


class MovieApiTests(TestCase):
    from django.test import TestCase
    from rest_framework.test import APIClient
    from rest_framework import status
    from cinema.models import Movie, Genre, Actor

    class MovieApiTests(TestCase):
        def setUp(self):
            self.client = APIClient()
            self.drama = Genre.objects.create(name="Drama")
            self.comedy = Genre.objects.create(name="Comedy")
            self.actress = Actor.objects.create(first_name="Kate", last_name="Winslet")
            self.movie = Movie.objects.create(title="Titanic", description="Desc", duration=123)
            self.movie.genres.add(self.drama, self.comedy)
            self.movie.actors.add(self.actress)

        def test_get_movies(self):
            response = self.client.get("/api/cinema/movies/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["results"][0]["title"], "Titanic")

        def test_get_movies_with_genres_filtering(self):
            response = self.client.get(f"/api/cinema/movies/?genres={self.comedy.id}")
            self.assertEqual(len(response.data["results"]), 1)

        def test_get_movies_with_actors_filtering(self):
            response = self.client.get(f"/api/cinema/movies/?actors={self.actress.id}")
            self.assertEqual(len(response.data["results"]), 1)

        def test_get_movies_with_title_filtering(self):
            response = self.client.get("/api/cinema/movies/?title=Titanic")
            self.assertEqual(len(response.data["results"]), 1)

        def test_post_movies(self):
            response = self.client.post(
                "/api/cinema/movies/",
                {
                    "title": "Superman",
                    "description": "Desc",
                    "duration": 100,
                    "actors": [self.actress.id],
                    "genres": [self.drama.id],
                },
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
