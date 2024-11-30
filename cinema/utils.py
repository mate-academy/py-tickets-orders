def params_to_int(params: str) -> list[int]:
    return [int(str_id) for str_id in params.split(",")]
