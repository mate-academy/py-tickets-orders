# Tickets and Orders API

Read [the guideline](https://github.com/mate-academy/py-task-guideline/blob/main/README.md) before starting.
- Використовуйте наступну команду, щоб завантажити підготовлені дані з приладу для тестування та налагодження коду:

  `python manage.py loaddata cinema_service_db_data.json`
 
- Після завантаження даних з приладу ви можете використовувати наступного суперкористувача (або створити іншого самостійно):
  - Логін: `admin.user`
  - Пароль: `1qazcde3

- У цьому завданні ви додасте функціонал роботи з замовленнями.

1. Створіть серіалізатори та подання для підтримки таких кінцевих точок:

* `GET api/cinema/orders/` — має повернути список усіх замовлень, відфільтрованих автентифікованим користувачем.
Додайте детальну інформацію про сеанс фільму та застосуйте розбивку на сторінки

Приклад:
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

* `POST api/cinema/orders/` - має створити нове замовлення для автентифікованого користувача.
Він повинен підтримувати таку структуру запиту:
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

2. Забезпечити фільтрацію фільмів за жанрами, акторами та назвою. Використовуйте параметри `?actors=`, `?genres=` і `?title=`.
Фільтрування за назвою за допомогою параметра `string` має повернути всі фільми, назва яких містить `string`.

3. Реалізуйте фільтрацію сеансів фільму за датою та фільмом. Дата має бути надана у форматі "рік-місяць-день",
фільм за його ідентифікатором.
Приклад:
```
GET /api/cinema/movie_sessions/?date=2022-12-12&movie=1
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


4. Повернути зайняті місця для кінцевої точки подробиць кіносеансу
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
5. Додайте поле `tickets_available` до кінцевої точки списку кіносеансів,
який говорить про те, скільки `квитків` ще доступно для кожного `movie_session`


Факультативні завдання:
- Забезпечте перевірку для створення квитків на рівні серіалізатора

### Note: Check your code using this [checklist](checklist.md) before pushing your solution.
