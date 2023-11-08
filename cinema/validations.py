def validate_seats_and_rows(
        row: int,
        seat: int,
        cinema_hall,
        exception_to_raise
) -> None:
    for ticket_attr_value, ticket_attr_name, cinema_hall_attr_name in [
        (row, "row", "rows"),
        (seat, "seat", "seats_in_row"),
    ]:
        count_attrs = getattr(
            cinema_hall, cinema_hall_attr_name
        )
        if not (1 <= ticket_attr_value <= count_attrs):
            raise exception_to_raise(
                {
                    ticket_attr_name: [f"{ticket_attr_name} "
                                       f"number must be in available range: "
                                       f"(1, {cinema_hall_attr_name}): "
                                       f"(1, {count_attrs})"]
                }
            )
