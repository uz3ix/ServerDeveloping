from models import UserCreate, LoginData
from fastapi.responses import FileResponse
from fastapi import Header, Response, Request, HTTPException, FastAPI
import uuid
from datetime import datetime
from itsdangerous import TimestampSigner, BadSignature
import time


app = FastAPI()

SECRET_KEY = "SUPER_SECRET_KEY"
signer = TimestampSigner(SECRET_KEY)
SESSION_LIFETIME = 300 
EXTEND_THRESHOLD = 180


fake_user = {
    "username": "user123",
    "password": "password123"
}

sessions = {}


@app.get("/health")
def health_check():
    return {"status": "200/Ok"}

@app.post("/create_user")
def create_user(user: UserCreate):
    return user

sample_products = [
    {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"product_id": 456, "name": "Phone Case", "category": "Accessories", "price": 19.99},
    {"product_id": 789, "name": "Iphone", "category": "Electronics", "price": 1299.99},
    {"product_id": 101, "name": "Headphones", "category": "Accessories", "price": 99.99},
    {"product_id": 202, "name": "Smartwatch", "category": "Electronics", "price": 299.99},
]

@app.get("/products/search")
def search_products(keyword: str, category: str = None, limit: int = 10):
    result = []

    for product in sample_products:
        if keyword.lower() in product["name"].lower():
            if category:
                if product["category"].lower() == category.lower():
                    result.append(product)
            else:
                result.append(product)

    return result[:limit]

@app.get("/product/{product_id}")
def get_product(product_id: int):
    for product in sample_products:
        if product["product_id"] == product_id:
            return product
    return {"detail": "Не найден"}



@app.post("/login")
def login(data: dict, response: Response):
    if data["username"] != fake_user["username"] or data["password"] != fake_user["password"]:
        raise HTTPException(status_code=401, detail="неверные учетные данные")

    user_id = str(uuid.uuid4())
    timestamp = int(time.time())

    value = f"{user_id}.{timestamp}"
    signed_value = signer.sign(value).decode()

    response.set_cookie(
        key="session_token",
        value=signed_value,
        httponly=True,
        max_age=SESSION_LIFETIME
    )

    return {"message": "успешный вход", "user_id": user_id}

@app.get("/user")
def get_user(request: Request):
    token = request.cookies.get("session_token")

    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Не авторизован")

    return {"username": sessions[token]}

@app.get("/profile")
def profile(request: Request, response: Response):
    token = request.cookies.get("session_token")

    if not token:
        raise HTTPException(status_code=401, detail="сессия не найдена")

    try:
        data = signer.unsign(token, max_age=SESSION_LIFETIME).decode()
    except BadSignature:
        raise HTTPException(status_code=401, detail="неверная сессия")

    try:
        user_id, timestamp = data.split(".")
        timestamp = int(timestamp)
    except:
        raise HTTPException(status_code=401, detail="неверный формат сессии")

    now = int(time.time())
    diff = now - timestamp

    if diff > SESSION_LIFETIME:
        raise HTTPException(status_code=401, detail="сессия истекла")

    if EXTEND_THRESHOLD <= diff <= SESSION_LIFETIME:
        new_timestamp = now
        new_value = f"{user_id}.{new_timestamp}"
        new_signed = signer.sign(new_value).decode()

        response.set_cookie(
            key="session_token",
            value=new_signed,
            httponly=True,
            max_age=SESSION_LIFETIME
        )

    return {
        "user_id": user_id,
        "message": "сессия действительна"
    }


@app.get("/headers")
def get_headers(request: Request):
    user_agent = request.headers.get("User-Agent")
    accept_language = request.headers.get("Accept-Language")

    if not user_agent or not accept_language:
        raise HTTPException(status_code=400, detail="заголовки User-Agent и Accept-Language обязательны")

    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }

@app.get("/headers2")
def headers2(user_agent: str = Header(...), accept_language: str = Header(...)):
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }


@app.get("/info")
def info(response: Response, user_agent: str = Header(...), accept_language: str = Header(...)):
    response.headers["X-Server-Time"] = datetime.now().isoformat()

    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": user_agent,
            "Accept-Language": accept_language
        }
    }

