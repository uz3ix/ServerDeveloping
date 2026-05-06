from itertools import count
from threading import Lock

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from exceptions import CustomExceptionA, CustomExceptionB
from models import Product
from schemas import ErrorResponse, ProductCreate, ProductOut, UserIn, UserOut, ValidatedUser


app = FastAPI(title="KR4 FastAPI")

users_db: dict[int, dict] = {}
_id_seq = count(start=1)
_id_lock = Lock()


def next_user_id() -> int:
    with _id_lock:
        return next(_id_seq)


def reset_users_state() -> None:
    global _id_seq
    with _id_lock:
        users_db.clear()
        _id_seq = count(start=1)


@app.exception_handler(CustomExceptionA)
async def custom_exception_a_handler(_, exc: CustomExceptionA):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(error_code="CUSTOM_A", message=exc.message).model_dump(),
    )


@app.exception_handler(CustomExceptionB)
async def custom_exception_b_handler(_, exc: CustomExceptionB):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(error_code="CUSTOM_B", message=exc.message).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details=exc.errors(),
        ).model_dump(),
    )


@app.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED, tags=["9.1 Alembic"])
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/products", response_model=list[ProductOut], tags=["9.1 Alembic"])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id).all()


@app.get("/products/{product_id}", response_model=ProductOut, tags=["9.1 Alembic"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/custom/a/{value}", response_model=dict, responses={400: {"model": ErrorResponse}}, tags=["10.1 Errors"])
def endpoint_a(value: int):
    if value < 0:
        raise CustomExceptionA("Value must be greater than or equal to zero")
    return {"value": value}


@app.get("/custom/b/{resource_id}", response_model=dict, responses={404: {"model": ErrorResponse}}, tags=["10.1 Errors"])
def endpoint_b(resource_id: int):
    if resource_id != 1:
        raise CustomExceptionB(f"Resource {resource_id} not found")
    return {"id": resource_id, "title": "Existing resource"}


@app.post("/validate-user", response_model=ValidatedUser, tags=["10.2 Validation"])
def validate_user(user: ValidatedUser):
    return user


@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["11 Tests"])
def create_user(user: UserIn):
    user_id = next_user_id()
    users_db[user_id] = user.model_dump()
    return {"id": user_id, **users_db[user_id]}


@app.get("/users/{user_id}", response_model=UserOut, tags=["11 Tests"])
def get_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user_id, **users_db[user_id]}


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["11 Tests"])
def delete_user(user_id: int):
    if users_db.pop(user_id, None) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
