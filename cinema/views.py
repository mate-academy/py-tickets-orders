from django.db.models import Count, F, Q
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket
)

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderSerializer,
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

    @staticmethod
    def params_to_int(qs):
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        queryset = self.queryset

        # filtering for movies by actors, genres or title
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_id = self.params_to_int(actors)
            queryset = queryset.filter(actors__id__in=actors_id)

        if genres:
            genres_id = self.params_to_int(genres)
            queryset = queryset.filter(genres__id__in=genres_id)

        if title:
            queryset = queryset.filter(title__icontains=title)

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

    @staticmethod
    def date_to_int(date):
        return [int(str_date) for str_date in date.split("-")]

    def get_queryset(self):
        queryset = self.queryset

        # tickets available feature

        if self.action == "list":

            queryset = (
                queryset
                .select_related("cinema_hall")
                .annotate(
                    tickets_available=F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                    - Count("tickets"))
            )

        # filtering for movie sessions by movie id and/or date of session

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if movie and date:
            queryset = queryset.filter(movie_id=int(movie))
            year_month_day = self.date_to_int(date)
            queryset = queryset.filter(
                show_time__year=year_month_day[0],
                show_time__month=year_month_day[1],
                show_time__day=year_month_day[2]
            )
            return queryset.distinct()

        if movie:
            queryset = queryset.filter(movie_id=int(movie))

        if date:
            year_month_day = self.date_to_int(date)
            queryset = queryset.filter(
                show_time__year=year_month_day[0],
                show_time__month=year_month_day[1],
                show_time__day=year_month_day[2]
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class OrderPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"
    max_page_size = 50


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related("tickets__movie_session")

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
