from datetime import datetime
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, models
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from cinema.models import CinemaHall, Movie, MovieSession, Order, Ticket
from user.models import User


ORDERS_URL = "/api/cinema/orders/"


class OrdersContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="first-customer")
        cls.other_user = User.objects.create(username="second-customer")
        cls.movie = Movie.objects.create(
            title="Arrival", description="A first contact story", duration=116
        )
        cls.hall = CinemaHall.objects.create(
            name="Blue", rows=3, seats_in_row=4
        )
        cls.session = MovieSession.objects.create(
            movie=cls.movie,
            cinema_hall=cls.hall,
            show_time=datetime(2026, 10, 10, 18, 30),
        )
        cls.other_session = MovieSession.objects.create(
            movie=cls.movie,
            cinema_hall=cls.hall,
            show_time=datetime(2026, 10, 11, 18, 30),
        )
        cls.order = Order.objects.create(user=cls.user)
        cls.ticket = Ticket.objects.create(
            movie_session=cls.session, order=cls.order, row=2, seat=2
        )
        cls.other_order = Order.objects.create(user=cls.other_user)
        cls.other_ticket = Ticket.objects.create(
            movie_session=cls.session, order=cls.other_order, row=2, seat=3
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def ticket_payload(self, row=1, seat=1, session=None):
        return {
            "row": row,
            "seat": seat,
            "movie_session": (session or self.session).pk,
        }

    def assert_rejected_without_writes(self, payload):
        order_ids = set(Order.objects.values_list("id", flat=True))
        ticket_ids = set(Ticket.objects.values_list("id", flat=True))
        response = self.client.post(ORDERS_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            set(Order.objects.values_list("id", flat=True)), order_ids
        )
        self.assertEqual(
            set(Ticket.objects.values_list("id", flat=True)), ticket_ids
        )
        return response

    def test_list_isolates_orders_and_count_by_authenticated_owner(self):
        response = self.client.get(ORDERS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(response.data), {"count", "next", "previous", "results"}
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            [order["id"] for order in response.data["results"]],
            [self.order.pk],
        )
        self.client.force_authenticate(self.other_user)
        other_response = self.client.get(ORDERS_URL)
        self.assertEqual(other_response.data["count"], 1)
        self.assertEqual(
            [order["id"] for order in other_response.data["results"]],
            [self.other_order.pk],
        )

    def test_list_has_exact_nested_ticket_and_session_summary(self):
        response = self.client.get(ORDERS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order = response.data["results"][0]
        self.assertEqual(set(order), {"id", "tickets", "created_at"})
        self.assertEqual(len(order["tickets"]), 1)
        ticket = order["tickets"][0]
        self.assertEqual(set(ticket), {"id", "row", "seat", "movie_session"})
        self.assertEqual(ticket["id"], self.ticket.pk)
        self.assertEqual((ticket["row"], ticket["seat"]), (2, 2))
        self.assertEqual(
            ticket["movie_session"],
            {
                "id": self.session.pk,
                "show_time": "2026-10-10T18:30:00",
                "movie_title": "Arrival",
                "cinema_hall_name": "Blue",
                "cinema_hall_capacity": 12,
            },
        )

    def test_create_saves_new_order_and_both_tickets(self):
        order_ids = set(Order.objects.values_list("id", flat=True))
        ticket_ids = set(Ticket.objects.values_list("id", flat=True))
        payload = {
            "tickets": [self.ticket_payload(), self.ticket_payload(seat=2)]
        }

        response = self.client.post(ORDERS_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn(response.data["id"], order_ids)
        self.assertEqual(Order.objects.count(), len(order_ids) + 1)
        self.assertEqual(Ticket.objects.count(), len(ticket_ids) + 2)
        order = Order.objects.get(pk=response.data["id"])
        self.assertEqual(order.user_id, self.user.pk)
        self.assertEqual(
            set(order.tickets.values_list("row", "seat", "movie_session_id")),
            {(1, 1, self.session.pk), (1, 2, self.session.pk)},
        )
        self.assertEqual(len(response.data["tickets"]), 2)
        self.assertEqual(
            {ticket["id"] for ticket in response.data["tickets"]},
            set(order.tickets.values_list("id", flat=True)),
        )
        self.assertTrue(
            ticket_ids.isdisjoint(order.tickets.values_list("id", flat=True))
        )

    def test_create_ignores_client_supplied_owner(self):
        response = self.client.post(
            ORDERS_URL,
            {"user": self.other_user.pk, "tickets": [self.ticket_payload()]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Order.objects.get(pk=response.data["id"]).user_id, self.user.pk
        )
        self.assertEqual(Order.objects.filter(user=self.other_user).count(), 1)

    def test_anonymous_list_and_create_are_forbidden_without_writes(self):
        self.client.force_authenticate(user=None)
        for method in ("get", "post"):
            with self.subTest(method=method):
                if method == "get":
                    response = self.client.get(ORDERS_URL)
                else:
                    response = self.client.post(
                        ORDERS_URL,
                        {"tickets": [self.ticket_payload()]},
                        format="json",
                    )
                self.assertEqual(
                    response.status_code, status.HTTP_403_FORBIDDEN
                )
                self.assertEqual(Order.objects.count(), 2)
                self.assertEqual(Ticket.objects.count(), 2)

    def test_pagination_has_stable_tie_breaking_and_owner_only_count(self):
        for _ in range(10):
            Order.objects.create(user=self.user)
        for _ in range(2):
            Order.objects.create(user=self.other_user)
        Order.objects.update(created_at=datetime(2026, 10, 9, 12, 0))
        expected_ids = list(
            Order.objects.filter(user=self.user)
            .order_by("-id")
            .values_list("id", flat=True)
        )

        first = self.client.get(ORDERS_URL)

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["count"], 11)
        self.assertEqual(len(first.data["results"]), 10)
        self.assertIsNone(first.data["previous"])
        self.assertEqual(
            parse_qs(urlparse(first.data["next"]).query), {"page": ["2"]}
        )
        second = self.client.get(first.data["next"])
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.data["count"], 11)
        self.assertEqual(len(second.data["results"]), 1)
        self.assertIsNone(second.data["next"])
        self.assertIsNotNone(second.data["previous"])
        combined_ids = [
            order["id"]
            for order in first.data["results"] + second.data["results"]
        ]
        self.assertEqual(combined_ids, expected_ids)
        previous = self.client.get(second.data["previous"])
        self.assertEqual(previous.data["results"], first.data["results"])

    def test_missing_or_empty_tickets_are_rejected(self):
        for payload in ({}, {"tickets": []}):
            with self.subTest(payload=payload):
                response = self.assert_rejected_without_writes(payload)
                self.assertIn("tickets", response.data)

    def test_missing_ticket_fields_are_rejected(self):
        for field in ("row", "seat", "movie_session"):
            with self.subTest(field=field):
                ticket = self.ticket_payload()
                del ticket[field]
                self.assert_rejected_without_writes({"tickets": [ticket]})

    def test_unknown_movie_session_is_rejected(self):
        ticket = self.ticket_payload()
        ticket["movie_session"] = 999999
        self.assert_rejected_without_writes({"tickets": [ticket]})

    def test_movie_session_id_outside_big_auto_field_range_rejected(self):
        self.client.raise_request_exception = False
        ticket = self.ticket_payload()
        ticket["movie_session"] = 2 ** 63
        self.assert_rejected_without_writes({"tickets": [ticket]})

    def test_first_and_last_hall_places_are_valid(self):
        response = self.client.post(
            ORDERS_URL,
            {
                "tickets": [
                    self.ticket_payload(row=1, seat=1),
                    self.ticket_payload(row=3, seat=4),
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            set(
                Ticket.objects.filter(order_id=response.data["id"])
                .values_list("row", "seat")
            ),
            {(1, 1), (3, 4)},
        )

    def test_negative_zero_and_out_of_range_places_are_rejected(self):
        for row, seat in ((-1, 1), (0, 1), (4, 1), (1, -1), (1, 0), (1, 5)):
            with self.subTest(row=row, seat=seat):
                self.assert_rejected_without_writes(
                    {"tickets": [self.ticket_payload(row=row, seat=seat)]}
                )

    def test_occupied_place_is_rejected(self):
        self.assert_rejected_without_writes(
            {"tickets": [self.ticket_payload(row=2, seat=3)]}
        )

    def test_duplicate_places_in_one_payload_are_rejected(self):
        self.assert_rejected_without_writes(
            {"tickets": [self.ticket_payload(), self.ticket_payload()]}
        )

    def test_same_coordinates_in_different_sessions_are_allowed(self):
        response = self.client.post(
            ORDERS_URL,
            {
                "tickets": [
                    self.ticket_payload(),
                    self.ticket_payload(session=self.other_session),
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            set(
                Ticket.objects.filter(order_id=response.data["id"])
                .values_list("row", "seat", "movie_session_id")
            ),
            {(1, 1, self.session.pk), (1, 1, self.other_session.pk)},
        )

    def test_save_validation_error_rolls_back_order_and_first_ticket(self):
        original_save = Ticket.save
        saved_ticket_ids = []

        def save_then_fail(ticket, *args, **kwargs):
            if saved_ticket_ids:
                raise DjangoValidationError({"seat": "Place was occupied."})
            original_save(ticket, *args, **kwargs)
            saved_ticket_ids.append(ticket.pk)
            self.assertTrue(Ticket.objects.filter(pk=ticket.pk).exists())

        with patch.object(Ticket, "save", new=save_then_fail):
            self.assert_rejected_without_writes(
                {
                    "tickets": [
                        self.ticket_payload(), self.ticket_payload(seat=2)
                    ]
                }
            )
        self.assertEqual(len(saved_ticket_ids), 1)

    def test_database_unique_error_rolls_back_order_and_first_ticket(self):
        original_save = Ticket.save
        saved_ticket_ids = []

        def create_database_conflict(ticket, *args, **kwargs):
            if saved_ticket_ids:
                ticket.row = 1
                ticket.seat = 1
                return models.Model.save(ticket, *args, **kwargs)
            original_save(ticket, *args, **kwargs)
            saved_ticket_ids.append(ticket.pk)
            self.assertTrue(Ticket.objects.filter(pk=ticket.pk).exists())

        with patch.object(Ticket, "save", new=create_database_conflict):
            self.assert_rejected_without_writes(
                {
                    "tickets": [
                        self.ticket_payload(), self.ticket_payload(seat=2)
                    ]
                }
            )
        self.assertEqual(len(saved_ticket_ids), 1)

    def test_unrelated_integrity_error_is_not_reported_as_bad_booking(self):
        original_save = Ticket.save
        saved_ticket_ids = []

        def save_then_fail(ticket, *args, **kwargs):
            if saved_ticket_ids:
                raise IntegrityError("CHECK constraint failed: unrelated")
            original_save(ticket, *args, **kwargs)
            saved_ticket_ids.append(ticket.pk)

        with patch.object(Ticket, "save", new=save_then_fail):
            with self.assertRaisesMessage(IntegrityError, "unrelated"):
                self.client.post(
                    ORDERS_URL,
                    {
                        "tickets": [
                            self.ticket_payload(), self.ticket_payload(seat=2)
                        ]
                    },
                    format="json",
                )
        self.assertEqual(len(saved_ticket_ids), 1)
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(Ticket.objects.count(), 2)
