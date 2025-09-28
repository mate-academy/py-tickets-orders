def query_param_value_to_split(key: str, params: dict):
    value: str | None = params.get(key, None)

    if value is not None:
        params = [n.strip() for n in value.split(",") if n.strip()]
        return [int(p) for p in params]

    return []
