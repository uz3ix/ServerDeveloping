from fastapi import Depends, Header, HTTPException, status

from app.schemas import CurrentUser
from app.storage import room_manager, task_storage


def get_current_user(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_user_role: str = Header(default="user", alias="X-User-Role"),
) -> CurrentUser:
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Id header is required",
        )

    try:
        user_id = int(x_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Id header must be an integer",
        ) from exc

    return CurrentUser(id=user_id, role=x_user_role)


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def get_storage():
    return task_storage


def get_room_manager():
    return room_manager
