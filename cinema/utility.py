def ids_str_to_int(ids: str) -> list[int]:
    return [int(str_id) for str_id in ids.split(",")]
