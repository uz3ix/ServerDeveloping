from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TaskStatus = Literal["todo", "in_progress", "done"]


class CurrentUser(BaseModel):
    id: int
    role: str = "user"


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=80)
    description: str | None = None
    status: TaskStatus
    priority: int = Field(ge=1, le=5)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskOut(TaskCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int


class UserOut(BaseModel):
    id: int
    role: str


class StatsOut(BaseModel):
    total_tasks: int
    by_status: dict[TaskStatus, int]


class HealthOut(BaseModel):
    status: str
    env: str


class RoomUsersOut(BaseModel):
    room_id: str
    users: list[str]


class JoinEvent(BaseModel):
    type: Literal["join"]
    room_id: str
    username: str


class ChatMessageIn(BaseModel):
    type: Literal["message"]
    text: str


class ChatMessageOut(BaseModel):
    type: Literal["message"]
    room_id: str
    username: str
    text: str


class ChatErrorOut(BaseModel):
    type: Literal["error"]
    detail: str

