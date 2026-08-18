from datetime import datetime
from django.db.models import Count, F
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.permissions import IsAdminOrIfAuthenticatedReadOnly
from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieListSerializer,
    MovieDetailSerializer,
    MovieImageSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieSessionDetailSerializer,
    OrderSerializer,
    OrderListSerializer,
)


class GenreViewSet(
    viewsets.mixins.CreateModelMixin,
    viewsets.mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class ActorViewSet(
    viewsets.mixins.CreateModelMixin,
    viewsets.mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class CinemaHallViewSet(
    viewsets.mixins.CreateModelMixin,
    viewsets.mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class MovieViewSet(
    viewsets.mixins.CreateModelMixin,
    viewsets.mixins.ListModelMixin,
    viewsets.mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == \"list\":
            return MovieListSerializer
        if self.action == \"retrieve\":
            return MovieDetailSerializer
        if self.action == \"upload_image\":
            return MovieImageSerializer
        return MovieSerializer

    def _params_to_ints(self, qs):
        return [int(str_id) for str_id in qs.split(\",\")]

    def get_queryset(self):
        queryset = self.queryset
        actors = self.request.query_params.get(\"actors\")
        genres = self.request.query_params.get(\"genres\")
        title = self.request.query_params.get(\"title\")

        if actors:
            actors_ids = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)
        if genres:
            genres_ids = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset.distinct()

    @action(
        methods=[\"POST\"],
        detail=True,
        url_path=\"upload-image\",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        movie = self.get_object()
        serializer = self.get_serializer(movie, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == \"list\":
            return MovieSessionListSerializer
        if self.action == \"retrieve\":
            return MovieSessionDetailSerializer
        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == \"list\":
            queryset = queryset.select_related(
                \"movie\", \"cinema_hall\"
            ).annotate(
                tickets_available=F(\"cinema_hall__rows\")
                * F(\"cinema_hall__seats_in_row\")
                - Count(\"tickets\")
            )
        elif self.action == \"retrieve\":
            queryset = queryset.select_related(\"movie\", \"cinema_hall\")

        date = self.request.query_params.get(\"date\")
        movie = self.request.query_params.get(\"movie\")

        if date:
            queryset = queryset.filter(show_time__date=date)
        if movie:
            queryset = queryset.filter(movie_id=movie)

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = \"page_size\"
    max_page_size = 100


class OrderViewSet(
    viewsets.mixins.CreateModelMixin,
    viewsets.mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == \"list\":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
