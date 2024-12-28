from rest_framework import viewsets

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
    OrderListSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    pagination_class = None


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def filter_queryset(self, queryset):
        """
        Apply filters for movies based on title, genres, and actors.
        """
        # Get query parameters
        title = self.request.query_params.get("title", None)
        genres = self.request.query_params.get("genres", None)
        actors = self.request.query_params.get("actors", None)

        # Filter by title (case-insensitive, partial match)
        if title:
            queryset = queryset.filter(title__icontains=title)

        # Filter by genres (comma-separated IDs)
        if genres:
            genre_ids = [int(id) for id in genres.split(",") if id.isdigit()]
            queryset = queryset.filter(genres__id__in=genre_ids)

        # Filter by actors (comma-separated IDs)
        if actors:
            actor_ids = [int(id) for id in actors.split(",") if id.isdigit()]
            queryset = queryset.filter(actors__id__in=actor_ids)

        # Remove duplicates caused by many-to-many relationships
        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def filter_queryset(self, queryset):
        date = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        if date:
            try:
                # Match only the date portion of show_time
                queryset = queryset.filter(show_time__date=date)
            except ValueError:
                queryset = queryset.none()

        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        return queryset.distinct()


class OrdersViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    #
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
