import os

from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect

from app.dependencies import get_room_manager
from app.routers import admin, tasks, users
from app.schemas import ChatErrorOut, ChatMessageIn, HealthOut, RoomUsersOut
from app.storage import RoomManager, room_manager, task_storage


app = FastAPI(
    title="KR5 FastAPI",
    openapi_tags=[
        {"name": "tasks", "description": "Task management endpoints"},
        {"name": "users", "description": "Current user endpoints"},
        {"name": "admin", "description": "Admin-only endpoints"},
        {"name": "rooms", "description": "Room inspection endpoints"},
        {"name": "health", "description": "Application health endpoint"},
    ],
)
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(admin.router)


@app.get("/health", response_model=HealthOut, tags=["health"])
def healthcheck():
    return {"status": "ok", "env": os.getenv("APP_ENV", "local")}


@app.get("/rooms/{room_id}/users", response_model=RoomUsersOut, tags=["rooms"])
def get_room_users(
    room_id: str,
    manager: RoomManager = Depends(get_room_manager),
):
    return {"room_id": room_id, "users": manager.get_users(room_id)}


@app.websocket("/ws/rooms/{room_id}")
async def websocket_room(
    websocket: WebSocket,
    room_id: str,
    username: str = Query(default=""),
    manager: RoomManager = Depends(get_room_manager),
):
    clean_username = username.strip()
    if not clean_username:
        await websocket.close(code=1008)
        return

    await manager.connect(room_id=room_id, username=clean_username, websocket=websocket)
    try:
        while True:
            payload = ChatMessageIn.model_validate(await websocket.receive_json())
            if len(payload.text) > 300:
                await websocket.send_json(
                    ChatErrorOut(type="error", detail="Message is too long").model_dump()
                )
                continue
            await manager.send_message(
                room_id=room_id,
                username=clean_username,
                text=payload.text,
            )
    except WebSocketDisconnect:
        await manager.disconnect(room_id=room_id, username=clean_username, websocket=websocket)


def reset_state() -> None:
    task_storage.reset()
    room_manager.reset()
