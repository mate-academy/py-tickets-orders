def params_to_int(query_string):
    try:
        return [int(el) for el in query_string.split(",")]
    except ValueError:
        return
