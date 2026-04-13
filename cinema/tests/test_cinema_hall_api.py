from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from cinema.models import CinemaHall


class CinemaHallApiTests(TestCase):
    from django.test import TestCase
    from rest_framework.test import APIClient
    from rest_framework import status
    from cinema.models import CinemaHall

    class CinemaHallApiTests(TestCase):
        def setUp(self):
            self.client = APIClient()
            CinemaHall.objects.create(name="Blue", rows=15, seats_in_row=20)
            CinemaHall.objects.create(name="VIP", rows=6, seats_in_row=8)

        def test_get_cinema_halls(self):
            response = self.client.get("/api/cinema/cinema_halls/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["results"][0]["name"], "Blue")
            self.assertEqual(response.data["results"][1]["name"], "VIP")

        def test_post_cinema_halls(self):
            response = self.client.post(
                "/api/cinema/cinema_halls/",
                {"name": "Yellow", "rows": 14, "seats_in_row": 15},
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(CinemaHall.objects.count(), 3)

        def test_get_cinema_hall(self):
            hall = CinemaHall.objects.get(name="VIP")
            response = self.client.get(f"/api/cinema/cinema_halls/{hall.id}/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["name"], "VIP")

        def test_patch_cinema_hall(self):
            hall = CinemaHall.objects.first()
            response = self.client.patch(f"/api/cinema/cinema_halls/{hall.id}/", {"name": "Green"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            hall.refresh_from_db()
            self.assertEqual(hall.name, "Green")
