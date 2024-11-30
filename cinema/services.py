def query_params_to_int_list(params: str) -> list[int]:
    return [int(param) for param in params.split(",")]
