def filter_request_to_int(query_params: str) -> list:
    return [int(str_id) for str_id in query_params.split(",")]
