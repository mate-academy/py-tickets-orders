from rest_framework import (
    viewsets,
    status,
    mixins,
)

from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
)

from rest_framework.response import Response

from cinema.models import (
    Actor,
    CinemaHall,
    Genre,
    Movie,
    MovieSession,
    Order,
)

from cinema.serializers import (
    ActorSerializer,
    CinemaHallSerializer,
    GenreSerializer,
    MovieListSerializer,
    MovieRetrieveSerializer,
    MovieSessionListSerializer,
    MovieSessionRetrieveSerializer,
    OrderListSerializer,
    OrderCreateSerializer,
    MovieSessionWriteSerializer,
    MovieWriteSerializer
)

from cinema.pagination import StandardResultsSetPagination


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = [AllowAny]


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    permission_classes = [AllowAny]


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.prefetch_related("genres", "actors")
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer
        if self.action == "retrieve":
            return MovieRetrieveSerializer
        return MovieWriteSerializer

    @staticmethod
    def _params_to_ints(qs: str | None) -> list[int] | None:
        if qs:
            return [int(str_id) for str_id in qs.split(",")]
        return None

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title")
        genres_ids_str = self.request.query_params.get("genres")
        actors_ids_str = self.request.query_params.get("actors")

        genres_ids = self._params_to_ints(genres_ids_str)
        actors_ids = self._params_to_ints(actors_ids_str)

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genres_ids:
            queryset = queryset.filter(genres__id__in=genres_ids)

        if actors_ids:
            queryset = queryset.filter(actors__id__in=actors_ids)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.select_related(
        "movie", "cinema_hall"
    ).prefetch_related("tickets")
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer
        if self.action == "retrieve":
            return MovieSessionRetrieveSerializer
        return MovieSessionWriteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        date_str = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        if date_str:
            queryset = queryset.filter(show_time__date=date_str)

        if movie_id:
            try:
                movie_id_int = int(movie_id)
                queryset = queryset.filter(movie_id=movie_id_int)
            except ValueError:
                pass

        return queryset


class OrderViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
):
    queryset = Order.objects.all()
    permission_classes = (IsAuthenticated,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderCreateSerializer

    def perform_create(self, serializer: OrderCreateSerializer) -> None:
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        order_instance = serializer.instance
        response_serializer = OrderListSerializer(order_instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
