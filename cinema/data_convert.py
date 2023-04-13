from django.db.models import QuerySet


def query_params_str_to_int(queryset: QuerySet) -> list:
    return [int(id_) for id_ in queryset.split(",")]
