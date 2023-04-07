def _params_to_ints(string: str) -> list[int]:
    return [int(str_id) for str_id in string.split(",")]
