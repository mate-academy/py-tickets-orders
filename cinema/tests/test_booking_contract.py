from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APIClient

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
    Ticket,
)


MOVIES_URL = "/api/cinema/movies/"
SESSIONS_URL = "/api/cinema/movie_sessions/"
ORDERS_URL = "/api/cinema/orders/"


class BookingFixtures(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="booking-owner"
        )
        self.client.force_authenticate(user=self.user)

    def create_movie(self, number):
        genre = Genre.objects.create(name=f"Genre {number}")
        actor = Actor.objects.create(
            first_name=f"Actor {number}", last_name="Example"
        )
        movie = Movie.objects.create(
            title=f"Movie {number}",
            description=f"Description {number}",
            duration=90 + number,
        )
        movie.genres.add(genre)
        movie.actors.add(actor)
        return movie

    def create_session(self, number, rows=2, seats_in_row=3):
        movie = self.create_movie(number)
        hall = CinemaHall.objects.create(
            name=f"Hall {number}", rows=rows, seats_in_row=seats_in_row
        )
        return MovieSession.objects.create(
            movie=movie,
            cinema_hall=hall,
            show_time=datetime(2026, 10, 10, 9) + timedelta(days=number),
        )

    def create_ticket(self, session, order, row, seat):
        return Ticket.objects.create(
            movie_session=session, order=order, row=row, seat=seat
        )

    def get_data(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def get_data_and_query_count(self, url):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
            response.render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data, len(queries)

    def assert_places(self, data, places):
        self.assertCountEqual(data["taken_places"], places)
        for place in data["taken_places"]:
            self.assertEqual(set(place), {"row", "seat"})

    def assert_session_summary(self, data, session):
        self.assertEqual(
            data,
            {
                "id": session.id,
                "show_time": session.show_time.isoformat(),
                "movie_title": session.movie.title,
                "cinema_hall_name": session.cinema_hall.name,
                "cinema_hall_capacity": session.cinema_hall.capacity,
            },
        )


class BookingApiContractTests(BookingFixtures):
    def setUp(self):
        super().setUp()
        self.session = self.create_session(1)
        self.other_session = self.create_session(2)
        self.order = Order.objects.create(user=self.user)

    def test_taken_places_include_only_row_and_seat_of_this_session(self):
        self.create_ticket(self.session, self.order, row=1, seat=2)
        self.create_ticket(self.session, self.order, row=2, seat=3)
        self.create_ticket(self.other_session, self.order, row=1, seat=2)
        self.create_ticket(self.other_session, self.order, row=2, seat=1)

        data = self.get_data(f"{SESSIONS_URL}{self.session.id}/")

        self.assert_places(
            data, [{"row": 1, "seat": 2}, {"row": 2, "seat": 3}]
        )

    def test_empty_session_has_no_taken_places(self):
        self.create_ticket(self.other_session, self.order, row=1, seat=1)

        data = self.get_data(f"{SESSIONS_URL}{self.session.id}/")

        self.assert_places(data, [])

    def test_available_tickets_for_empty_partial_and_full_sessions(self):
        partial_session = self.create_session(3)
        full_session = self.create_session(4)
        self.create_ticket(partial_session, self.order, row=1, seat=1)
        self.create_ticket(partial_session, self.order, row=2, seat=3)
        for row in range(1, 3):
            for seat in range(1, 4):
                self.create_ticket(full_session, self.order, row, seat)
        for seat in range(1, 4):
            self.create_ticket(self.other_session, self.order, 1, seat)

        data = self.get_data(SESSIONS_URL)
        self.assertIsInstance(data, list)
        available = {
            item["id"]: item["tickets_available"] for item in data
        }

        self.assertEqual(
            available,
            {
                self.session.id: 6,
                partial_session.id: 4,
                full_session.id: 0,
                self.other_session.id: 3,
            },
        )

    def test_post_order_updates_places_and_available_ticket_count(self):
        self.create_ticket(self.session, self.order, row=1, seat=1)
        self.create_ticket(self.other_session, self.order, row=2, seat=3)
        before = self.get_data(SESSIONS_URL)
        before_available = {
            item["id"]: item["tickets_available"] for item in before
        }
        payload = {
            "tickets": [
                {"row": 1, "seat": 2, "movie_session": self.session.id},
                {"row": 2, "seat": 1, "movie_session": self.session.id},
            ]
        }

        response = self.client.post(ORDERS_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        saved_tickets = Ticket.objects.filter(
            order_id=response.data["id"]
        ).values_list("movie_session_id", "row", "seat")
        self.assertCountEqual(
            saved_tickets,
            [(self.session.id, 1, 2), (self.session.id, 2, 1)],
        )
        self.assertEqual(
            Order.objects.get(id=response.data["id"]).user_id, self.user.id
        )
        after = self.get_data(SESSIONS_URL)
        after_available = {
            item["id"]: item["tickets_available"] for item in after
        }
        self.assertEqual(before_available[self.session.id], 5)
        self.assertEqual(after_available[self.session.id], 3)
        self.assertEqual(
            after_available[self.other_session.id],
            before_available[self.other_session.id],
        )
        detail = self.get_data(f"{SESSIONS_URL}{self.session.id}/")
        self.assert_places(
            detail,
            [
                {"row": 1, "seat": 1},
                {"row": 1, "seat": 2},
                {"row": 2, "seat": 1},
            ],
        )

    def test_order_read_has_five_session_summary_fields(self):
        ticket = self.create_ticket(
            self.session, self.order, row=2, seat=3
        )

        data = self.get_data(ORDERS_URL)

        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["results"]), 1)
        order = data["results"][0]
        self.assertEqual(set(order), {"id", "created_at", "tickets"})
        self.assertEqual(order["id"], self.order.id)
        self.assertEqual(len(order["tickets"]), 1)
        ticket_data = order["tickets"][0]
        self.assertEqual(
            set(ticket_data), {"id", "row", "seat", "movie_session"}
        )
        self.assertEqual(ticket_data["id"], ticket.id)
        self.assertEqual(ticket_data["row"], 2)
        self.assertEqual(ticket_data["seat"], 3)
        self.assert_session_summary(
            ticket_data["movie_session"], self.session
        )

    def test_previous_five_lists_keep_all_records_in_arrays(self):
        for number in range(3, 13):
            self.create_session(number)
        endpoints = (
            ("/api/cinema/genres/", Genre),
            ("/api/cinema/actors/", Actor),
            ("/api/cinema/cinema_halls/", CinemaHall),
            (MOVIES_URL, Movie),
            (SESSIONS_URL, MovieSession),
        )

        for url, model in endpoints:
            with self.subTest(url=url):
                expected_ids = set(
                    model.objects.values_list("id", flat=True)
                )
                self.assertGreater(len(expected_ids), 10)

                data = self.get_data(url)

                self.assertIsInstance(data, list)
                self.assertEqual(
                    {item["id"] for item in data}, expected_ids
                )


class BookingQueryContractTests(BookingFixtures):
    def assert_constant_query_count(self, small_count, expanded_count):
        self.assertGreater(small_count, 0)
        self.assertEqual(
            expanded_count,
            small_count,
            "The number of GET queries must not grow with related records.",
        )

    def test_movie_list_queries_do_not_grow_per_movie(self):
        first_movie = self.create_movie(1)

        small_data, small_count = self.get_data_and_query_count(MOVIES_URL)

        self.assertEqual([item["id"] for item in small_data], [first_movie.id])
        movies = [first_movie] + [
            self.create_movie(number) for number in range(2, 6)
        ]

        expanded_data, expanded_count = self.get_data_and_query_count(
            MOVIES_URL
        )

        self.assertEqual(
            {item["id"] for item in expanded_data},
            {movie.id for movie in movies},
        )
        for item in expanded_data:
            number = int(item["title"].split()[-1])
            self.assertEqual(item["genres"], [f"Genre {number}"])
            self.assertEqual(item["actors"], [f"Actor {number} Example"])
        self.assert_constant_query_count(small_count, expanded_count)

    def test_session_list_queries_do_not_grow_per_session(self):
        order = Order.objects.create(user=self.user)
        first_session = self.create_session(1)
        self.create_ticket(first_session, order, row=1, seat=1)

        small_data, small_count = self.get_data_and_query_count(SESSIONS_URL)

        self.assertEqual(
            [item["id"] for item in small_data], [first_session.id]
        )
        self.assertEqual(small_data[0]["tickets_available"], 5)
        sessions = [first_session]
        available = {first_session.id: 5}
        for number in range(2, 6):
            session = self.create_session(number)
            sessions.append(session)
            for seat in range(1, 4):
                self.create_ticket(session, order, row=1, seat=seat)
            available[session.id] = 3

        expanded_data, expanded_count = self.get_data_and_query_count(
            SESSIONS_URL
        )

        self.assertEqual(
            {item["id"] for item in expanded_data},
            {session.id for session in sessions},
        )
        self.assertEqual(
            {
                item["id"]: item["tickets_available"]
                for item in expanded_data
            },
            available,
        )
        self.assert_constant_query_count(small_count, expanded_count)

    def test_session_detail_queries_do_not_grow_with_related_data(self):
        session = self.create_session(1, seats_in_row=5)
        order = Order.objects.create(user=self.user)
        self.create_ticket(session, order, row=1, seat=1)
        detail_url = f"{SESSIONS_URL}{session.id}/"

        small_data, small_count = self.get_data_and_query_count(detail_url)

        self.assert_places(small_data, [{"row": 1, "seat": 1}])
        expected_genres = ["Genre 1"]
        expected_actors = ["Actor 1 Example"]
        for number in range(2, 6):
            self.create_ticket(session, order, row=1, seat=number)
            genre = Genre.objects.create(name=f"Extra genre {number}")
            actor = Actor.objects.create(
                first_name=f"Extra actor {number}", last_name="Example"
            )
            session.movie.genres.add(genre)
            session.movie.actors.add(actor)
            expected_genres.append(genre.name)
            expected_actors.append(actor.full_name)
        other_session = self.create_session(2)
        self.create_ticket(other_session, order, row=2, seat=1)

        expanded_data, expanded_count = self.get_data_and_query_count(
            detail_url
        )

        self.assert_places(
            expanded_data,
            [{"row": 1, "seat": seat} for seat in range(1, 6)],
        )
        self.assertCountEqual(
            expanded_data["movie"]["genres"], expected_genres
        )
        self.assertCountEqual(
            expanded_data["movie"]["actors"], expected_actors
        )
        self.assert_constant_query_count(small_count, expanded_count)

    def test_order_list_queries_do_not_grow_per_order_or_ticket(self):
        first_session = self.create_session(1)
        first_order = Order.objects.create(user=self.user)
        first_ticket = self.create_ticket(
            first_session, first_order, row=1, seat=1
        )

        small_data, small_count = self.get_data_and_query_count(ORDERS_URL)

        self.assertEqual(small_data["count"], 1)
        self.assertEqual(len(small_data["results"]), 1)
        self.assertEqual(small_data["results"][0]["id"], first_order.id)
        orders = [first_order]
        tickets = [first_ticket]
        sessions = {first_session.id: first_session}
        for seat in range(2, 4):
            tickets.append(
                self.create_ticket(first_session, first_order, 1, seat)
            )
        for number in range(2, 6):
            session = self.create_session(number)
            sessions[session.id] = session
            order = Order.objects.create(user=self.user)
            orders.append(order)
            for seat in range(1, 4):
                tickets.append(self.create_ticket(session, order, 1, seat))

        expanded_data, expanded_count = self.get_data_and_query_count(
            ORDERS_URL
        )

        self.assertEqual(expanded_data["count"], 5)
        self.assertIsNone(expanded_data["next"])
        self.assertEqual(
            {item["id"] for item in expanded_data["results"]},
            {order.id for order in orders},
        )
        returned_tickets = [
            ticket
            for order in expanded_data["results"]
            for ticket in order["tickets"]
        ]
        self.assertEqual(
            {ticket["id"] for ticket in returned_tickets},
            {ticket.id for ticket in tickets},
        )
        for ticket in returned_tickets:
            summary = ticket["movie_session"]
            self.assert_session_summary(summary, sessions[summary["id"]])
        self.assert_constant_query_count(small_count, expanded_count)
