from django.db.models import QuerySet
from rest_framework.request import Request


def params_to_ints(params: str) -> list[int]:
    if not params:
        return []

    return list(map(int, params.split(",")))


class QueryParamsToQuerySet:
    def __init__(self, queryset: QuerySet, request: Request):
        self._queryset = queryset
        self._request = request

    def apply(
        self,
        parameter_name: str,
        queryset_lookup: str,
        parameter_default_value: any = None,
        parameter_exists_checker: callable = lambda parameter: parameter,
        param_transformer: callable = lambda x: x,
    ):
        parameter = self._request.query_params.get(
            parameter_name, parameter_default_value
        )

        if parameter_exists_checker(parameter):
            parameter = param_transformer(parameter)
            self._queryset = self._queryset.filter(
                **{queryset_lookup: parameter}
            )

        return self

    @property
    def queryset(self):
        return self._queryset
