from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.schemas import CurrentUser, UserOut


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: CurrentUser = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, current_user: CurrentUser = Depends(get_current_user)):
    role = current_user.role if user_id == current_user.id else "user"
    return UserOut(id=user_id, role=role)

