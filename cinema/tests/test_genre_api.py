from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from cinema.models import Genre
from user.models import User


class GenreApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(username="testuser")
        self.client.force_authenticate(user=self.user)

        self.comedy_genre = Genre.objects.create(name="Comedy")
        self.drama_genre = Genre.objects.create(name="Drama")

    def test_get_genres(self) -> None:
        response = self.client.get("/api/cinema/genres/")
        genres = [genre["name"] for genre in response.data['results']]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(sorted(genres), ["Comedy", "Drama"])

    def test_post_genres(self) -> None:
        response = self.client.post(
            "/api/cinema/genres/",
            {
                "name": "Sci-fi",
            },
        )
        db_genres = Genre.objects.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(db_genres.count(), 3)
        self.assertTrue(db_genres.filter(name="Sci-fi").exists())

    def test_get_invalid_genre(self) -> None:
        response = self.client.get("/api/cinema/genres/1001/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_genre(self) -> None:
        response = self.client.put(
            f"/api/cinema/genres/{self.comedy_genre.id}/",
            {
                "name": "Sci-fi",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.comedy_genre.refresh_from_db()
        self.assertEqual(self.comedy_genre.name, "Sci-fi")

    def test_delete_genre(self) -> None:
        response = self.client.delete(f"/api/cinema/genres/{self.comedy_genre.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(Genre.objects.count(), 1)
        self.assertFalse(Genre.objects.filter(id=self.comedy_genre.id).exists())

    def test_delete_invalid_genre(self) -> None:
        response = self.client.delete(
            "/api/cinema/genres/1000/",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
