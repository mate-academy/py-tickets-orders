from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from .models import *
from .serializers import *


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
    def str_to_int(list_s):
        return [int(nums) for nums in list_s.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")
        title = self.request.query_params.get("title")

        if genres:
            self.queryset = self.queryset.filter(genres__id__in=self.str_to_int(genres))

        if actors:
            self.queryset = self.queryset.filter(actors__id__in=self.str_to_int(actors))

        if title:
            self.queryset = self.queryset.filter(title__icontains=title)

        return self.queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        date = self.request.query_params.get("date")
        movies_id = self.request.query_params.get("movie")
        self.queryset = self.queryset.select_related("cinema_hall", "movie")

        if date:
            date = date.split("-")
            self.queryset = self.queryset.filter(show_time__year=date[0],
                                                 show_time__month=date[1],
                                                 show_time__day=date[2])
        if movies_id:
            movies_id = [int(num) for num in movies_id.split(",")]
            self.queryset = self.queryset.filter(movie_id__in=movies_id)

        if self.action == "list":
            self.queryset = (
                self.queryset
                .prefetch_related("tickets")
                .annotate(
                    tickets_available=F("cinema_hall__seats_in_row") * F("cinema_hall__rows") - Count("tickets"))
            )

        return self.queryset


class OrderPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related("tickets__movie_session__cinema_hall")\
                .prefetch_related("tickets__movie_session__movie")
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer
