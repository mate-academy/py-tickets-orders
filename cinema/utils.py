from datetime import datetime


def params_to_ints(query_string):
    return [int(str_id) for str_id in query_string.split(",")]


def params_to_date(query_string):
    return [
        datetime.strptime(str_date, "%Y-%m-%d").date()
        for str_date in query_string.split(",")
    ]
