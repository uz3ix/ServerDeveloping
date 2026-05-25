from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_current_user, get_storage
from app.schemas import CurrentUser, TaskCreate, TaskOut, TaskStatus, TaskStatusUpdate
from app.storage import TaskStorage


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    current_user: CurrentUser = Depends(get_current_user),
    storage: TaskStorage = Depends(get_storage),
):
    return storage.create_task(task_in=task_in, owner_id=current_user.id)


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status: TaskStatus | None = None,
    min_priority: int | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    storage: TaskStorage = Depends(get_storage),
):
    return storage.list_tasks(
        owner_id=current_user.id,
        status_filter=status,
        min_priority=min_priority,
    )


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    storage: TaskStorage = Depends(get_storage),
):
    task = storage.get_owned_task(task_id=task_id, owner_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int,
    payload: TaskStatusUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    storage: TaskStorage = Depends(get_storage),
):
    task = storage.update_status(task_id=task_id, owner_id=current_user.id, status=payload.status)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    storage: TaskStorage = Depends(get_storage),
):
    if not storage.delete_owned_task(task_id=task_id, owner_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

