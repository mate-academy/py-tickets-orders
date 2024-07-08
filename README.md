# Tickets and Orders API

Read [the guideline](https://github.com/mate-academy/py-task-guideline/blob/main/README.md) before starting.
- Use the following command to load prepared data from fixture to test and debug your code:

  `python manage.py loaddata cinema_service_db_data.json`
 
- After loading data from fixture you can use following superuser (or create another one by yourself):
  - Login: `admin.user`
  - Password: `1qazcde3`

`In this task you will add the functionality of working with orders.

1. Create serializers and views to support the following endpoints:

* `GET api/cinema/orders/` - should return a list of the all orders that filtered by the authenticated user.
Add detail information about movie session and implement pagination.

Example:
```
GET /api/cinema/orders/?page=2
```

```
HTTP 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "count": 3,
    "next": "http://127.0.0.1:8000/api/cinema/orders/?page=3",
    "previous": "http://127.0.0.1:8000/api/cinema/orders/",
    "results": [
        {
            "id": 2,
            "tickets": [
                {
                    "id": 2,
                    "row": 2,
                    "seat": 3,
                    "movie_session": {
                        "id": 1,
                        "show_time": "2022-12-12T12:32:00Z",
                        "movie_title": "Movie",
                        "cinema_hall_name": "Green",
                        "cinema_hall_capacity": 2829
                    }
                }
            ],
            "created_at": "2022-05-16T13:45:30.911367Z"
        }
    ]
}
```

* `POST api/cinema/orders/` - should create a new order for the authenticated user. 
It should support the following request structure:
```json
{
    "tickets": [
        {
            "row": 2,
            "seat": 1,
            "movie_session": 1
        },
        {
            "row": 2,
            "seat": 2,
            "movie_session": 1
        }
    ]
}
```

2. Provide filtering for movies by genres, actors and title. Use `?actors=`, `?genres=` and `?title=` parameters.
Filtering by title with the `string` parameter should return all movies whose title contains `string`.

3. Implement filtering for movie sessions by date and movie. The date should be provided in `year-month-day` format, 
the movie by its id.
Example:
```
GET /api/cinema/movie_sessions/?date=2022-1-12&movie=1
```
```
HTTP 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

[
    {
        "id": 1,
        "show_time": "2022-12-12T12:32:00Z",
        "movie_title": "Movie",
        "cinema_hall_name": "Green",
        "cinema_hall_capacity": 2829
    }
]
```


4. Return taken places for movie session details endpoint
```
GET /api/cinema/movie_sessions/1/
```
```
HTTP 200 OK
Allow: GET, PUT, PATCH, DELETE, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "id": 1,
    "show_time": "2022-12-12T12:32:00Z",
    "movie": {
        "id": 1,
        "title": "Movie",
        "description": "description",
        "duration": 123,
        "genres": [
            "drama"
        ],
        "actors": [
            "F F"
        ]
    },
    "cinema_hall": {
        "id": 1,
        "name": "Green",
        "rows": 123,
        "seats_in_row": 23,
        "capacity": 2829
    },
    "taken_places": [
        {
            "row": 2,
            "seat": 1
        },
        {
            "row": 2,
            "seat": 3
        },
        {
            "row": 2,
            "seat": 10
        }
    ]
}

```
5. Add `tickets_available` field to movie sessions list endpoint, 
which says about how many `tickets` are still available for each `movie_session`


Optional tasks:
- Provide validation for creating tickets on serializer level

### Note: Check your code using this [checklist](checklist.md) before pushing your solution.
