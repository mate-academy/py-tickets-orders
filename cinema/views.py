from django.http import Http404
from rest_framework import viewsets, status
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from cinema.models import (
    Genre,
    Actor,
    CinemaHall,
    Movie,
    MovieSession,
    Order,
    Ticket,
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save()


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    filter_backends = [SearchFilter]
    search_fields = ["title"]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        elif self.action == "retrieve":
            return MovieDetailSerializer
        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        actors = self.request.query_params.getlist("actors", [])
        genres = self.request.query_params.getlist("genres", [])
        title = self.request.query_params.get("title", None)

        if actors:
            queryset = queryset.filter(actors__id__in=actors)

        if genres:
            try:
                genre_ids = [int(genre_id) for genre_id in genres]
                queryset = queryset.filter(genres__id__in=genre_ids)
            except ValueError:
                raise Http404("Invalid genre ID provided.")

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()


class MovieSessionFilter(DjangoFilterBackend):
    def filter_queryset(self, request, queryset, view):
        date_param = request.query_params.get("date")
        movie_param = request.query_params.get("movie")

        if date_param:
            queryset = queryset.filter(show_time__date=date_param)

        if movie_param:
            queryset = queryset.filter(movie__id=movie_param)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    filter_backends = [SearchFilter]
    filterset_fields = ["show_time", "movie"]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        return MovieSessionDetailSerializer

    def get_queryset(self):
        queryset = self.queryset
        date_param = self.request.query_params.get("date")
        movie_param = self.request.query_params.get("movie")

        if date_param:
            queryset = queryset.filter(show_time__date=date_param)
        if movie_param:
            queryset = queryset.filter(movie__id=movie_param)

        return queryset


class MovieSessionDetailViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionDetailSerializer
    lookup_field = "pk"


class OrderPagination(PageNumberPagination):
    page_size = 10


class OrderListView(ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.filter(user=user)
        return queryset


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
