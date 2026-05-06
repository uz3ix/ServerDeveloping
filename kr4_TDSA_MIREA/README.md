# КР №4 — Технологии разработки серверных приложений

## Установка

```bash
pip install -r requirements.txt
```

## Миграции Alembic

```bash
alembic upgrade head
python scripts/seed_products.py
```

В проекте есть две миграции:

- `001_create_products.py` создает таблицу `products` с полями `id`, `title`, `price`, `count`.
- `002_add_product_description.py` добавляет обязательное поле `description`.

## Запуск приложения

```bash
uvicorn main:app --reload
```

Swagger UI будет доступен по адресу:

```text
http://127.0.0.1:8000/docs
```

## Проверка API

```bash
curl -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"title":"Monitor","price":12990,"count":5,"description":"27 inch display"}'

curl http://127.0.0.1:8000/custom/a/-1
curl http://127.0.0.1:8000/custom/b/404

curl -X POST http://127.0.0.1:8000/validate-user \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","age":21,"email":"alice@example.com","password":"secret123"}'

curl -X POST http://127.0.0.1:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username":"john","age":30}'
```

## Тесты

```bash
pytest
```

Тесты покрывают:

- пользовательские исключения и формат ошибок;
- пользовательскую обработку ошибок валидации;
- синхронный CRUD пользователей через `TestClient`;
- асинхронные тесты пользователей через `pytest-asyncio`, `httpx.AsyncClient`, `ASGITransport` и `Faker`.
