from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from cinema.models import CinemaHall
from user.models import User

class CinemaHallApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username="admin")
        self.client.force_authenticate(user=self.user)
        CinemaHall.objects.create(name="Blue", rows=15, seats_in_row=20)
        CinemaHall.objects.create(name="VIP", rows=6, seats_in_row=8)

    def test_get_cinema_halls(self):
        response = self.client.get("/api/cinema/cinema_halls/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["name"], "Blue")
        self.assertEqual(response.data[0]["rows"], 15)
        self.assertEqual(response.data[0]["seats_in_row"], 20)
        self.assertEqual(response.data[1]["name"], "VIP")
        self.assertEqual(response.data[1]["rows"], 6)
        self.assertEqual(response.data[1]["seats_in_row"], 8)

    def test_post_cinema_halls(self):
        response = self.client.post("/api/cinema/cinema_halls/", {"name": "Yellow", "rows": 14, "seats_in_row": 15})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CinemaHall.objects.filter(name="Yellow").count(), 1)

    def test_get_cinema_hall(self):
        response = self.client.get("/api/cinema/cinema_halls/2/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "VIP")

    def test_get_invalid_cinema_hall(self):
        response = self.client.get("/api/cinema/cinema_halls/1001/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_cinema_hall(self):
        response = self.client.put("/api/cinema/cinema_halls/1/", {"name": "Yellow", "rows": 14, "seats_in_row": 15})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        hall = CinemaHall.objects.get(pk=1)
        self.assertEqual([hall.name, hall.rows, hall.seats_in_row], ["Yellow", 14, 15])

    def test_patch_cinema_hall(self):
        response = self.client.patch("/api/cinema/cinema_halls/1/", {"name": "Green"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CinemaHall.objects.get(id=1).name, "Green")

    def test_delete_cinema_hall(self):
        response = self.client.delete("/api/cinema/cinema_halls/1/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CinemaHall.objects.filter(id=1).count(), 0)

    def test_delete_invalid_cinema_hall(self):
        response = self.client.delete("/api/cinema/cinema_halls/1000/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
