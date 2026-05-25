from collections import Counter, defaultdict
from copy import deepcopy
from threading import Lock

from fastapi import WebSocket

from app.schemas import ChatMessageOut, JoinEvent, TaskCreate, TaskOut


class TaskStorage:
    def __init__(self) -> None:
        self._tasks: dict[int, TaskOut] = {}
        self._next_id = 1
        self._lock = Lock()

    def reset(self) -> None:
        with self._lock:
            self._tasks.clear()
            self._next_id = 1

    def create_task(self, task_in: TaskCreate, owner_id: int) -> TaskOut:
        with self._lock:
            task = TaskOut(id=self._next_id, owner_id=owner_id, **task_in.model_dump())
            self._tasks[self._next_id] = task
            self._next_id += 1
            return task.model_copy(deep=True)

    def list_tasks(
        self,
        owner_id: int,
        status_filter: str | None = None,
        min_priority: int | None = None,
    ) -> list[TaskOut]:
        tasks = [
            task.model_copy(deep=True)
            for task in self._tasks.values()
            if task.owner_id == owner_id
        ]
        if status_filter is not None:
            tasks = [task for task in tasks if task.status == status_filter]
        if min_priority is not None:
            tasks = [task for task in tasks if task.priority >= min_priority]
        return sorted(tasks, key=lambda item: item.id)

    def get_owned_task(self, task_id: int, owner_id: int) -> TaskOut | None:
        task = self._tasks.get(task_id)
        if task is None or task.owner_id != owner_id:
            return None
        return task.model_copy(deep=True)

    def update_status(self, task_id: int, owner_id: int, status: str) -> TaskOut | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.owner_id != owner_id:
                return None
            updated = task.model_copy(update={"status": status}, deep=True)
            self._tasks[task_id] = updated
            return updated.model_copy(deep=True)

    def delete_owned_task(self, task_id: int, owner_id: int) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.owner_id != owner_id:
                return False
            del self._tasks[task_id]
            return True

    def delete_any_task(self, task_id: int) -> bool:
        with self._lock:
            if task_id not in self._tasks:
                return False
            del self._tasks[task_id]
            return True

    def stats(self) -> dict:
        counter = Counter(task.status for task in self._tasks.values())
        return {
            "total_tasks": len(self._tasks),
            "by_status": {
                "todo": counter.get("todo", 0),
                "in_progress": counter.get("in_progress", 0),
                "done": counter.get("done", 0),
            },
        }


class RoomManager:
    def __init__(self) -> None:
        self._rooms: dict[str, list[tuple[str, WebSocket]]] = defaultdict(list)

    def reset(self) -> None:
        self._rooms.clear()

    async def connect(self, room_id: str, username: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms[room_id].append((username, websocket))
        await self.broadcast(
            room_id,
            JoinEvent(type="join", room_id=room_id, username=username).model_dump(),
        )

    async def disconnect(self, room_id: str, username: str, websocket: WebSocket) -> None:
        connections = self._rooms.get(room_id, [])
        self._rooms[room_id] = [
            (name, socket)
            for name, socket in connections
            if socket is not websocket or name != username
        ]
        if not self._rooms[room_id]:
            self._rooms.pop(room_id, None)

    async def broadcast(self, room_id: str, payload: dict) -> None:
        for _, websocket in list(self._rooms.get(room_id, [])):
            await websocket.send_json(payload)

    def get_users(self, room_id: str) -> list[str]:
        return [username for username, _ in self._rooms.get(room_id, [])]

    async def send_message(self, room_id: str, username: str, text: str) -> None:
        payload = ChatMessageOut(
            type="message",
            room_id=room_id,
            username=username,
            text=text,
        ).model_dump()
        await self.broadcast(room_id, payload)


task_storage = TaskStorage()
room_manager = RoomManager()

