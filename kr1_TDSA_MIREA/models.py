from pydantic import BaseModel, Field, field_validator
import re

BAD_PATTERN = re.compile(r"(кринж\w*|рофл\w*|вайб\w*)", flags=re.IGNORECASE)

class CalcIn(BaseModel):
    num1: float
    num2: float

class User(BaseModel):
    name: str
    id: int

class UserWithAge(BaseModel):
    name: str
    age: int

class Feedback(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    message: str = Field(..., min_length=10, max_length=500)

    @field_validator("message")
    @classmethod
    def no_bad_words(cls, v: str) -> str:
        if BAD_PATTERN.search(v):
            raise ValueError("Использование недопустимых слов")
        return v
