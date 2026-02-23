from fastapi import FastAPI
from models import User, CalcIn, UserWithAge, Feedback
from fastapi.responses import FileResponse


app = FastAPI()

@app.get("/task1")
def root():
    return {"message": "Добро пожаловать в моё приложение FastAPI!"}

@app.get("/")
def index():
    return FileResponse("index.html", media_type="text/html")

@app.post("/calculate")
def calculate(data: CalcIn):
    return {"result": data.num1 + data.num2}


user ={
    "name": 'artur',
    'id': 1
}

@app.get("/users")
def get_user():
    return user

users = [
   {"name": "artur", "age": 26},
]

@app.post("/user")
def create_user(user: UserWithAge):
    is_adult = user.age >= 18
    users.append(user)
    return {
        "name": user.name,
        "age": user.age,
        "is_adult": is_adult
    }

feedbacks: list[Feedback] = []

@app.post("/feedback")
def create_feedback(data: Feedback):
    feedbacks.append(data)
    return {"message": f"Спасибо, {data.name}! Ваш отзыв сохранён."}

