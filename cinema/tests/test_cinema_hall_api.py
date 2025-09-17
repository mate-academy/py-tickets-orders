from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from cinema.models import CinemaHall
from user.models import User


class CinemaHallApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(username="testuser")
        self.client.force_authenticate(user=self.user)
        self.blue_hall = CinemaHall.objects.create(
            name="Blue",
            rows=15,
            seats_in_row=20,
        )
        self.vip_hall = CinemaHall.objects.create(
            name="VIP",
            rows=6,
            seats_in_row=8,
        )

    def test_get_cinema_halls(self) -> None:
        response = self.client.get("/api/cinema/cinema_halls/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data['results']

        self.assertEqual(results[0]["name"], self.blue_hall.name)
        self.assertEqual(results[0]["rows"], self.blue_hall.rows)
        self.assertEqual(results[0]["seats_in_row"], self.blue_hall.seats_in_row)

        self.assertEqual(results[1]["name"], self.vip_hall.name)
        self.assertEqual(results[1]["rows"], self.vip_hall.rows)
        self.assertEqual(results[1]["seats_in_row"], self.vip_hall.seats_in_row)

    def test_post_cinema_halls(self) -> None:
        payload = {
            "name": "Yellow",
            "rows": 14,
            "seats_in_row": 15,
        }
        response = self.client.post("/api/cinema/cinema_halls/", payload)
        db_cinema_halls = CinemaHall.objects.all()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(db_cinema_halls.count(), 3)
        self.assertEqual(db_cinema_halls.filter(name="Yellow").count(), 1)

    def test_get_cinema_hall(self) -> None:
        response = self.client.get(f"/api/cinema/cinema_halls/{self.vip_hall.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.vip_hall.name)
        self.assertEqual(response.data["rows"], self.vip_hall.rows)
        self.assertEqual(response.data["seats_in_row"], self.vip_hall.seats_in_row)

    def test_get_invalid_cinema_hall(self) -> None:
        response = self.client.get("/api/cinema/cinema_halls/1001/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_cinema_hall(self) -> None:
        payload = {
            "name": "Yellow",
            "rows": 14,
            "seats_in_row": 15,
        }
        response = self.client.put(f"/api/cinema/cinema_halls/{self.blue_hall.id}/", payload)
        self.blue_hall.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.blue_hall.name, "Yellow")
        self.assertEqual(self.blue_hall.rows, 14)
        self.assertEqual(self.blue_hall.seats_in_row, 15)

    def test_patch_cinema_hall(self) -> None:
        payload = {
            "name": "Green",
        }
        response = self.client.patch(f"/api/cinema/cinema_halls/{self.blue_hall.id}/", payload)
        self.blue_hall.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.blue_hall.name, "Green")

    def test_delete_cinema_hall(self) -> None:
        response = self.client.delete(f"/api/cinema/cinema_halls/{self.blue_hall.id}/")
        db_cinema_halls_id_1 = CinemaHall.objects.filter(id=self.blue_hall.id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(db_cinema_halls_id_1.count(), 0)
        self.assertEqual(CinemaHall.objects.count(), 1)

    def test_delete_invalid_cinema_hall(self) -> None:
        response = self.client.delete(
            "/api/cinema/cinema_halls/1000/",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
