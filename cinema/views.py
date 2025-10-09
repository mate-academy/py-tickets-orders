from django.db.models import Count, F, Q
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
    MovieListSerializer,
    OrderSerializer,
    OrderCreateSerializer,
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

    def get_queryset(self):
        queryset = self.queryset
        actors_params = self.request.query_params.get("actors")
        genres_params = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors_params:
            ids, names = [], []
            for token in actors_params.split(","):
                token = token.strip()
                if not token:
                    continue
                try:
                    ids.append(int(token))
                except ValueError:
                    names.append(token)
            query = Q()
            if ids:
                query |= Q(actors__id__in=ids)
            if names:
                query |= Q(actors__full_name__in=names)

            if query:
                queryset = queryset.filter(query).distinct()
        if genres_params:
            if genres_params:
                ids, names = [], []
                for token in genres_params.split(","):
                    token = token.strip()
                    if not token:
                        continue
                    try:
                        ids.append(int(token))
                    except ValueError:
                        names.append(token)
                query = Q()
                if ids:
                    query |= Q(genres__id__in=ids)
                if names:
                    query |= Q(genres__full_name__in=names)

                if query:
                    queryset = queryset.filter(query).distinct()
        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors")

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
        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if movie:
            movie_ids = [int(str_id) for str_id in movie.split(",")]
            queryset = queryset.filter(movie_id__in=movie_ids)
        if date:
            queryset = queryset.filter(show_time__date=date)

        if self.action == "list":
            queryset = queryset.prefetch_related("movie", "cinema_hall")

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderResultsSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 10


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
    pagination_class = OrderResultsSetPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer_class = OrderCreateSerializer
        if self.action == "list":
            serializer_class = OrderSerializer
        return serializer_class
