import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_user_async(async_client, faker):
    payload = {"username": faker.user_name(), "age": faker.random_int(min=19, max=80)}

    response = await async_client.post("/users", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["username"] == payload["username"]
    assert body["age"] == payload["age"]


@pytest.mark.asyncio
async def test_get_existing_user_async(async_client, faker):
    payload = {"username": faker.user_name(), "age": faker.random_int(min=19, max=80)}
    created = await async_client.post("/users", json=payload)
    user_id = created.json()["id"]

    response = await async_client.get(f"/users/{user_id}")

    assert response.status_code == 200
    assert response.json() == {"id": user_id, **payload}


@pytest.mark.asyncio
async def test_get_missing_user_async(async_client):
    response = await async_client.get("/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_delete_existing_user_async(async_client, faker):
    payload = {"username": faker.user_name(), "age": faker.random_int(min=19, max=80)}
    created = await async_client.post("/users", json=payload)
    user_id = created.json()["id"]

    response = await async_client.delete(f"/users/{user_id}")

    assert response.status_code == 204
    assert response.content == b""


@pytest.mark.asyncio
async def test_delete_same_user_twice_async(async_client, faker):
    payload = {"username": faker.user_name(), "age": faker.random_int(min=19, max=80)}
    created = await async_client.post("/users", json=payload)
    user_id = created.json()["id"]

    first_delete = await async_client.delete(f"/users/{user_id}")
    second_delete = await async_client.delete(f"/users/{user_id}")

    assert first_delete.status_code == 204
    assert second_delete.status_code == 404
