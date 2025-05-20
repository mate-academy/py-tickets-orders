from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from cinema.models import Movie, Genre, Actor


class MovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.drama = Genre.objects.create(
            name="Drama",
        )
        self.comedy = Genre.objects.create(
            name="Comedy",
        )
        self.actress = Actor.objects.create(
            first_name="Kate", last_name="Winslet"
        )
        self.movie = Movie.objects.create(
            title="Titanic",
            description="Titanic description",
            duration=123,
        )
        self.movie.genres.add(self.drama)
        self.movie.genres.add(self.comedy)
        self.movie.actors.add(self.actress)

    def test_get_movies(self):
        response = self.client.get("/api/cinema/movies/")
        titanic = {
            "title": "Titanic",
            "description": "Titanic description",
            "duration": 123,
            "genres": ["Comedy", "Drama"],
            "actors": ["Kate Winslet"],
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        movies_data = response.data["results"]
        self.assertEqual(len(movies_data), 1)
        movie_in_response = movies_data[0]
        self.assertEqual(movie_in_response["title"], titanic["title"])
        self.assertEqual(
            movie_in_response["description"],
            titanic["description"]
        )
        self.assertEqual(movie_in_response["duration"], titanic["duration"])
        self.assertEqual(
            sorted(movie_in_response["genres"]),
            sorted(titanic["genres"])
        )
        self.assertEqual(
            sorted(movie_in_response["actors"]),
            sorted(titanic["actors"])
        )

    def test_get_movies_with_genres_filtering(self):
        response = self.client.get(
            f"/api/cinema/movies/?genres={self.comedy.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

        url_params = f"genres={self.comedy.id}, {self.drama.id + 100}"
        response = self.client.get(
            f"/api/cinema/movies/?{url_params}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get("/api/cinema/movies/?genres=123213")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_movies_with_actors_filtering(self):
        response = self.client.get(
            f"/api/cinema/movies/?actors={self.actress.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get("/api/cinema/movies/?actors=123")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_movies_with_title_filtering(self):
        response = self.client.get("/api/cinema/movies/?title=ita")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get("/api/cinema/movies/?title=ati")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 0)

    def test_post_movies(self):
        response = self.client.post(
            "/api/cinema/movies/",
            {
                "title": "Superman",
                "description": "Superman description",
                "duration": 123,
                "actors": [self.actress.id],
                "genres": [self.drama.id, self.comedy.id],
            },
        )
        db_movies = Movie.objects.all()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(db_movies.count(), 2)
        self.assertEqual(db_movies.filter(title="Superman").count(), 1)

    def test_post_invalid_movies(self):
        response = self.client.post(
            "/api/cinema/movies/",
            {
                "title": "Superman",
                "description": "Superman description",
                "duration": 123,
                "actors": [
                    {
                        "id": 3,
                    }
                ],
            },
        )
        superman_movies = Movie.objects.filter(title="Superman")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(superman_movies.count(), 0)

    def test_get_movie(self):
        movie_to_get = Movie.objects.order_by("id").first()
        self.assertIsNotNone(movie_to_get)
        response = self.client.get(f"/api/cinema/movies/{movie_to_get.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Titanic")
        self.assertEqual(response.data["description"], "Titanic description")
        self.assertEqual(response.data["duration"], 123)

        response_genres = [genre["name"] for genre in response.data["genres"]]
        self.assertEqual(sorted(response_genres), ["Comedy", "Drama"])

        response_actors = [
            actor["full_name"] for actor in response.data["actors"]
        ]
        self.assertEqual(sorted(response_actors), ["Kate Winslet"])

    def test_get_invalid_movie(self):
        response = self.client.get("/api/cinema/movies/100/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_movie(self):
        movie_to_update = Movie.objects.order_by("id").first()
        self.assertIsNotNone(movie_to_update)
        response = self.client.put(
            f"/api/cinema/movies/{movie_to_update.id}/",
            {
                "title": "Watchman",
                "description": "Watchman description",
                "duration": 321,
                "genres": [self.drama.id, self.comedy.id],
                "actors": [self.actress.id],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_movie = Movie.objects.get(id=movie_to_update.id)
        self.assertEqual(db_movie.title, "Watchman")
        self.assertEqual(db_movie.description, "Watchman description")

    def test_delete_movie(self):
        movie_to_delete = Movie.objects.order_by("id").first()
        self.assertIsNotNone(movie_to_delete)
        response = self.client.delete(
            f"/api/cinema/movies/{movie_to_delete.id}/",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        db_movies_id_1 = Movie.objects.filter(id=movie_to_delete.id)
        self.assertEqual(db_movies_id_1.count(), 0)

    def test_delete_invalid_movie(self):
        response = self.client.delete(
            "/api/cinema/movies/1000/",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
