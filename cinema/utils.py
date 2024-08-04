def params_to_ints(query_string):
    return [int(str_id) for str_id in query_string.split(",")]
