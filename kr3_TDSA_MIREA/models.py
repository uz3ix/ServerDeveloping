from pydantic import BaseModel
from typing import Optional


# --- Задание 6.2: Модели пользователей ---

class UserBase(BaseModel):
    username: str

class User(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

# --- Задание 6.4 / 6.5: Модель для JWT логина ---

class LoginData(BaseModel):
    username: str
    password: str

# --- Задание 7.1: Модель с ролью ---

class UserWithRole(BaseModel):
    username: str
    password: str
    role: str = "guest"  # admin, user, guest

# --- Задание 8.2: Todo модели ---

class TodoCreate(BaseModel):
    title: str
    description: str

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
