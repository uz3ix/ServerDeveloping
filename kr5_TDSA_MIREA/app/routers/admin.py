from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_storage, require_admin
from app.schemas import CurrentUser, StatsOut
from app.storage import TaskStorage


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=StatsOut)
def get_stats(
    _: CurrentUser = Depends(require_admin),
    storage: TaskStorage = Depends(get_storage),
):
    return storage.stats()


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_any_task(
    task_id: int,
    _: CurrentUser = Depends(require_admin),
    storage: TaskStorage = Depends(get_storage),
):
    if not storage.delete_any_task(task_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

