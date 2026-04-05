# КР №3 — Технологии разработки серверных приложений

## Установка и запуск

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

## Переменные окружения

Скопируй `.env.example` → `.env` и настрой:

| Переменная    | По умолчанию          | Описание                        |
|---------------|-----------------------|---------------------------------|
| `MODE`        | `DEV`                 | Режим: `DEV` или `PROD`         |
| `DOCS_USER`   | `admin`               | Логин для /docs (только DEV)    |
| `DOCS_PASSWORD` | `secret`            | Пароль для /docs (только DEV)   |
| `JWT_SECRET`  | `super_jwt_secret_key`| Секрет для подписи JWT          |

---

## Задание 6.1 — Basic Auth (GET /login)

```bash
# Успешный вход
curl -u user123:password123 http://localhost:8000/login

# Неверные данные
curl -u user123:wrong http://localhost:8000/login
```

---

## Задание 6.2 — Хеширование паролей (POST /register, GET /login/secure)

```bash
# Регистрация
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"qwerty123"}'

# Вход
curl -u alice:qwerty123 http://localhost:8000/login/secure

# Неверный пароль
curl -u alice:wrongpass http://localhost:8000/login/secure
```

---

## Задание 6.3 — Управление документацией (MODE)

**DEV-режим** — /docs доступен только по логину/паролю:
```bash
curl -u admin:secret http://localhost:8000/docs
curl http://localhost:8000/docs  # → 401
```

**PROD-режим** — /docs полностью скрыт:
```bash
MODE=PROD uvicorn main:app --reload
curl http://localhost:8000/docs  # → 404
```

---

## Задание 6.4 — JWT (POST /jwt/login, GET /protected_resource)

```bash
# Сначала зарегистрируйся через /register (задание 6.2)
# Потом логинься через JWT
curl -X POST http://localhost:8000/jwt/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"qwerty123"}'

# Используй токен
curl http://localhost:8000/protected_resource \
  -H "Authorization: Bearer <токен>"
```

---

## Задание 6.5 — JWT + Rate Limiting

```bash
# Регистрация (1 раз в минуту)
curl -X POST http://localhost:8000/v2/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"qwerty123"}'

# Вход (5 раз в минуту)
curl -X POST http://localhost:8000/v2/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"qwerty123"}'
```

---

## Задание 7.1 — RBAC (роли: admin, user, guest)

Тестовые пользователи:
| Логин        | Пароль   | Роль  |
|--------------|----------|-------|
| admin_user   | admin123 | admin |
| regular_user | user123  | user  |
| guest_user   | guest123 | guest |

```bash
# Чтение (все роли)
curl -u guest_user:guest123 http://localhost:8000/rbac/resource

# Создание (только admin)
curl -u admin_user:admin123 -X POST http://localhost:8000/rbac/resource

# Создание от имени user → 403
curl -u regular_user:user123 -X POST http://localhost:8000/rbac/resource

# Защищённый ресурс (admin и user)
curl -u regular_user:user123 http://localhost:8000/rbac/protected_resource
curl -u guest_user:guest123 http://localhost:8000/rbac/protected_resource  # → 403
```

---

## Задание 8.1 — SQLite /db/register

```bash
curl -X POST http://localhost:8000/db/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","password":"12345"}'
```

---

## Задание 8.2 — CRUD Todo

```bash
# Создать
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy groceries","description":"Milk, eggs, bread"}'

# Получить по id
curl http://localhost:8000/todos/1

# Получить все
curl http://localhost:8000/todos

# Обновить
curl -X PUT http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed":true}'

# Удалить
curl -X DELETE http://localhost:8000/todos/1
```
