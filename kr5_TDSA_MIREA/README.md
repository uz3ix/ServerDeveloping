# Контрольная работа №5

Проект продолжает идеи `kr4_TDSA_MIREA`, но вынесен в отдельную папку `kr5_TDSA_MIREA` и перестроен под требования контрольной работы №5.

## Структура

```text
app/
  main.py
  dependencies.py
  schemas.py
  storage.py
  routers/
    tasks.py
    users.py
    admin.py
tests/
```

## Локальный запуск

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Тесты

```bash
pytest
```

## Docker

```bash
docker compose up --build
```

## Полезные маршруты

- `GET /health`
- `POST /tasks`
- `GET /tasks`
- `GET /users/me`
- `GET /admin/stats`
- `GET /rooms/{room_id}/users`
- `WS /ws/rooms/{room_id}?username=alice`
