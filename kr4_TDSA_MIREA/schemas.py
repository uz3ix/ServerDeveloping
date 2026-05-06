from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, conint, constr


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: list[dict] | None = None


class ProductCreate(BaseModel):
    title: str
    price: float
    count: int
    description: str


class ProductOut(ProductCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ValidatedUser(BaseModel):
    username: str
    age: conint(gt=18)
    email: EmailStr
    password: constr(min_length=8, max_length=16)
    phone: Optional[str] = "Unknown"


class UserIn(BaseModel):
    username: str
    age: int


class UserOut(UserIn):
    id: int
