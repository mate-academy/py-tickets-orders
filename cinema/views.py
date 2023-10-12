from datetime import datetime

from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, OrderSerializer, OrderListSerializer,
    TicketSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


    # filtering

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        queryset = self.queryset

        actors = self.request.query_params.get("actors")
        # Якщо у рядку браузера є https://27.0.0.1:8000/pi/station/buses/?facilities=1,2
        if actors:
            # тоді дістаю id
            actors_ids = self._params_to_ints(actors)
            # По всім автобусам дивлюся які є facilities і вибираю такі автобуси у якх одна з facilities є у списку facilities_ids
            queryset = Movie.objects.filter(actors__id__in=actors_ids)

        # ?genres =
        genres = self.request.query_params.get("genres")
        # Якщо у рядку браузера є https://27.0.0.1:8000/pi/station/buses/?facilities=1,2
        if genres:
            # тоді дістаю id
            genres_ids = self._params_to_ints(genres)
            # По всім автобусам дивлюся які є facilities і вибираю такі автобуси у якх одна з facilities є у списку facilities_ids
            queryset = Movie.objects.filter(genres__id__in=genres_ids)

        # ?title =
        title = self.request.query_params.get("title")
        if title:
            title_str = title
            queryset = Movie.objects.filter(title__icontains=title_str)
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        # ?movie =
        movie = self.request.query_params.get("movie")
        if movie:
            movie_id = int(movie)
            queryset = queryset.filter(movie__id=movie_id)


        # ?date =
        # ?data=2024-10-13

        date = self.request.query_params.get("date")

        if date:
            date_d = date.split("-")
            # date = datetime.date(date)
            # date = datetime.strptime(date_str, date_format)
            # queryset = queryset.filter(show_time=date)
            queryset = queryset.filter(
                show_time__year=date_d[0],
                show_time__month=date_d[1],
                show_time__day=date_d[2]
            )

        # tickets_available
        if self.action == "list":
            queryset = (
                queryset
                .select_related("cinema_hall")
                .annotate(tickets_available=F("cinema-hall__seats_in_row") - Count("tickets"))
            ).order_by("id")
            # queryset = (
            #     queryset
            #     .select_related("cinema_hall")
            #     .annotate(tickets_available=F("cinema_hall_capacity") - Count("tickets"))
            # ).order_by("id")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

# implement pagination
class OrderPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    # implement pagination
    pagination_class = OrderPagination

    # start Fix n+1 problem
    def get_queryset(self):
        # return a list of the all orders that filtered by the authenticated user
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":

            queryset = queryset.prefetch_related("tickets__movie_session__cinema_hall")# 9 SQL
        return queryset



    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return TicketSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


