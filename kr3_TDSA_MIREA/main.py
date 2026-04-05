import os
import secrets
import time
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from database import get_db_connection, init_db
from models import LoginData, TodoCreate, TodoUpdate, User, UserInDB, UserWithRole


MODE = os.getenv("MODE", "DEV").upper()
DOCS_USER = os.getenv("DOCS_USER", "admin")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "secret")

if MODE not in ("DEV", "PROD"):
    raise ValueError(f"Недопустимое значение MODE='{MODE}'. Допустимые: DEV, PROD")

if MODE == "PROD":
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
else:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "super_jwt_secret_key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 30


fake_users_db: dict[str, UserInDB] = {}


users_with_roles_db: dict[str, dict] = {
    "admin_user": {
        "username": "admin_user",
        "hashed_password": "", 
        "role": "admin",
    },
    "regular_user": {
        "username": "regular_user",
        "hashed_password": "",
        "role": "user",
    },
    "guest_user": {
        "username": "guest_user",
        "hashed_password": "",
        "role": "guest",
    },
}



@app.on_event("startup")
def startup():
    init_db()

    users_with_roles_db["admin_user"]["hashed_password"] = pwd_context.hash("admin123")
    users_with_roles_db["regular_user"]["hashed_password"] = pwd_context.hash("user123")
    users_with_roles_db["guest_user"]["hashed_password"] = pwd_context.hash("guest123")




security = HTTPBasic()


def verify_docs_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, DOCS_USER)
    correct_pass = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные данные для доступа к документации",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


if MODE == "DEV":
    @app.get("/docs", include_in_schema=False)
    def custom_docs(credentials: HTTPBasicCredentials = Depends(verify_docs_credentials)):
        return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")

    @app.get("/openapi.json", include_in_schema=False)
    def custom_openapi(credentials: HTTPBasicCredentials = Depends(verify_docs_credentials)):
        return get_openapi(title=app.title, version=app.version, routes=app.routes)

elif MODE == "PROD":
    @app.get("/docs", include_in_schema=False)
    @app.get("/openapi.json", include_in_schema=False)
    @app.get("/redoc", include_in_schema=False)
    def docs_not_found():
        raise HTTPException(status_code=404, detail="Not Found")



BASIC_USER = "user123"
BASIC_PASSWORD = "password123"


def authenticate_basic(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, BASIC_USER)
    correct_pass = secrets.compare_digest(credentials.password, BASIC_PASSWORD)
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учётные данные",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/login", tags=["6.1 Basic Auth"])
def login_basic(username: str = Depends(authenticate_basic)):
    return {"message": "You got my secret, welcome", "username": username}



def auth_user(credentials: HTTPBasicCredentials = Depends(security)) -> UserInDB:
    username = credentials.username
    password = credentials.password


    found_user = None
    for stored_username, user in fake_users_db.items():
        if secrets.compare_digest(stored_username, username):
            found_user = user
            break

    if not found_user or not pwd_context.verify(password, found_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учётные данные",
            headers={"WWW-Authenticate": "Basic"},
        )
    return found_user


@app.post("/register", tags=["6.2 Hashed Passwords"])
def register(user: User):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    hashed = pwd_context.hash(user.password)
    fake_users_db[user.username] = UserInDB(
        username=user.username,
        hashed_password=hashed,
    )
    return {"message": f"Пользователь '{user.username}' успешно зарегистрирован"}


@app.get("/login/secure", tags=["6.2 Hashed Passwords"])
def login_secure(current_user: UserInDB = Depends(auth_user)):
    return {"message": f"Welcome, {current_user.username}!"}


def create_jwt_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Неверный формат токена")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истёк")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")


def authenticate_user_stub(username: str, password: str) -> bool:
    if username in fake_users_db:
        return pwd_context.verify(password, fake_users_db[username].hashed_password)
    return False


@app.post("/jwt/login", tags=["6.4 JWT"])
def jwt_login(data: LoginData):
    if not authenticate_user_stub(data.username, data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_jwt_token(data.username)
    return {"access_token": token}


@app.get("/protected_resource", tags=["6.4 JWT"])
def protected_resource(username: str = Depends(verify_jwt_token)):
    return {"message": "Access granted", "username": username}



@app.post("/v2/register", status_code=201, tags=["6.5 JWT + Rate Limiting"])
@limiter.limit("1/minute")
def register_v2(request: Request, user: User):
    if user.username in fake_users_db:
        raise HTTPException(status_code=409, detail="User already exists")

    hashed = pwd_context.hash(user.password)
    fake_users_db[user.username] = UserInDB(
        username=user.username,
        hashed_password=hashed,
    )
    return {"message": "New user created"}


@app.post("/v2/login", tags=["6.5 JWT + Rate Limiting"])
@limiter.limit("5/minute")
def login_v2(request: Request, data: LoginData):
    found_user = None
    for stored_username, user in fake_users_db.items():
        if secrets.compare_digest(stored_username, data.username):
            found_user = user
            break

    if found_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not pwd_context.verify(data.password, found_user.hashed_password):
        raise HTTPException(status_code=401, detail="Authorization failed")

    token = create_jwt_token(data.username)
    return {"access_token": token, "token_type": "bearer"}



ROLE_PERMISSIONS = {
    "admin": ["create", "read", "update", "delete"],
    "user":  ["read", "update"],
    "guest": ["read"],
}


def get_rbac_user(credentials: HTTPBasicCredentials = Depends(security)) -> dict:
    found = None
    for stored_name, user_data in users_with_roles_db.items():
        if secrets.compare_digest(stored_name, credentials.username):
            found = user_data
            break

    if not found or not pwd_context.verify(credentials.password, found["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учётные данные",
            headers={"WWW-Authenticate": "Basic"},
        )
    return found


def require_permission(permission: str):
    def checker(user: dict = Depends(get_rbac_user)):
        role = user["role"]
        if permission not in ROLE_PERMISSIONS.get(role, []):
            raise HTTPException(
                status_code=403,
                detail=f"Роль '{role}' не имеет права '{permission}'"
            )
        return user
    return checker


@app.get("/rbac/resource", tags=["7.1 RBAC"])
def rbac_read(user: dict = Depends(require_permission("read"))):
    return {"message": f"Чтение доступно. Ваша роль: {user['role']}"}


@app.post("/rbac/resource", tags=["7.1 RBAC"])
def rbac_create(user: dict = Depends(require_permission("create"))):
    return {"message": f"Ресурс создан. Ваша роль: {user['role']}"}


@app.put("/rbac/resource", tags=["7.1 RBAC"])
def rbac_update(user: dict = Depends(require_permission("update"))):
    return {"message": f"Ресурс обновлён. Ваша роль: {user['role']}"}


@app.delete("/rbac/resource", tags=["7.1 RBAC"])
def rbac_delete(user: dict = Depends(require_permission("delete"))):
    return {"message": f"Ресурс удалён. Ваша роль: {user['role']}"}


@app.get("/rbac/protected_resource", tags=["7.1 RBAC"])
def rbac_protected(user: dict = Depends(require_permission("read"))):
    role = user["role"]
    if role not in ("admin", "user"):
        raise HTTPException(status_code=403, detail="Доступ только для admin и user")
    return {"message": "Доступ разрешён", "username": user["username"], "role": role}




@app.post("/db/register", tags=["8.1 SQLite Register"])
def db_register(user: User):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (user.username, user.password),
    )
    conn.commit()
    conn.close()
    return {"message": "User registered successfully!"}




@app.post("/todos", status_code=201, tags=["8.2 Todo CRUD"])
def create_todo(todo: TodoCreate):
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO todos (title, description, completed) VALUES (?, ?, 0)",
        (todo.title, todo.description),
    )
    todo_id = cursor.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "completed": bool(row["completed"]),
    }


@app.get("/todos/{todo_id}", tags=["8.2 Todo CRUD"])
def get_todo(todo_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Todo не найден")
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "completed": bool(row["completed"]),
    }


@app.get("/todos", tags=["8.2 Todo CRUD"])
def get_all_todos():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM todos").fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "description": r["description"],
            "completed": bool(r["completed"]),
        }
        for r in rows
    ]


@app.put("/todos/{todo_id}", tags=["8.2 Todo CRUD"])
def update_todo(todo_id: int, todo: TodoUpdate):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Todo не найден")

    title = todo.title if todo.title is not None else row["title"]
    description = todo.description if todo.description is not None else row["description"]
    completed = int(todo.completed) if todo.completed is not None else row["completed"]

    conn.execute(
        "UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?",
        (title, description, completed, todo_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    return {
        "id": updated["id"],
        "title": updated["title"],
        "description": updated["description"],
        "completed": bool(updated["completed"]),
    }


@app.delete("/todos/{todo_id}", tags=["8.2 Todo CRUD"])
def delete_todo(todo_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Todo не найден")
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return {"message": f"Todo {todo_id} успешно удалён"}
