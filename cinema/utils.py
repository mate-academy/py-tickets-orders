from django.http import QueryDict


def split_param_ids(obj: str) -> list[int]:
    if not obj:
        return []

    return [int(param) for param in obj.split(",")]


def extract_param_ids(
        query_params: QueryDict,
        field_name: str
) -> dict[str, int]:
    result = {}

    data = split_param_ids(query_params.get(field_name, ""))
    if not data:
        return result

    result[f"{field_name}__in"] = []
    for obj_id in data:
        result[f"{field_name}__in"].append(obj_id)

    return result
