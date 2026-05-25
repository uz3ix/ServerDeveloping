def create_task(client, user_id, title, status, priority):
    return client.post(
        "/tasks",
        headers={"X-User-Id": str(user_id)},
        json={
            "title": title,
            "description": None,
            "status": status,
            "priority": priority,
        },
    )


def test_users_me_returns_current_user(client):
    response = client.get("/users/me", headers={"X-User-Id": "10", "X-User-Role": "admin"})

    assert response.status_code == 200
    assert response.json() == {"id": 10, "role": "admin"}


def test_users_me_requires_user_header(client):
    response = client.get("/users/me")

    assert response.status_code == 401


def test_regular_user_gets_403_on_admin_stats(client):
    response = client.get("/admin/stats", headers={"X-User-Id": "10", "X-User-Role": "user"})

    assert response.status_code == 403


def test_admin_gets_stats_for_all_tasks(client):
    create_task(client, 10, "Task one", "todo", 1)
    create_task(client, 10, "Task two", "done", 3)
    create_task(client, 20, "Task tri", "in_progress", 5)

    response = client.get("/admin/stats", headers={"X-User-Id": "99", "X-User-Role": "admin"})

    assert response.status_code == 200
    assert response.json() == {
        "total_tasks": 3,
        "by_status": {"todo": 1, "in_progress": 1, "done": 1},
    }


def test_regular_user_cannot_delete_foreign_task(client):
    create_task(client, 10, "Task one", "todo", 1)

    response = client.delete("/tasks/1", headers={"X-User-Id": "20"})

    assert response.status_code == 404


def test_admin_can_delete_foreign_task(client):
    create_task(client, 10, "Task one", "todo", 1)

    delete_response = client.delete(
        "/admin/tasks/1",
        headers={"X-User-Id": "99", "X-User-Role": "admin"},
    )
    get_response = client.get("/tasks/1", headers={"X-User-Id": "10"})

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_openapi_groups_routes_by_tags(client):
    response = client.get("/openapi.json")
    tags = {tag["name"] for tag in response.json()["tags"]}

    assert {"tasks", "users", "admin"}.issubset(tags)

