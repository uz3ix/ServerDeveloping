def test_create_task_success(client):
    response = client.post(
        "/tasks",
        headers={"X-User-Id": "10"},
        json={
            "title": "Подготовить тесты",
            "description": "Написать интеграционные тесты",
            "status": "todo",
            "priority": 4,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "title": "Подготовить тесты",
        "description": "Написать интеграционные тесты",
        "status": "todo",
        "priority": 4,
        "owner_id": 10,
    }


def test_create_task_short_title_returns_422(client):
    response = client.post(
        "/tasks",
        headers={"X-User-Id": "10"},
        json={"title": "ab", "description": None, "status": "todo", "priority": 3},
    )

    assert response.status_code == 422


def test_missing_user_header_returns_401(client):
    response = client.get("/tasks")

    assert response.status_code == 401
    assert response.json()["detail"] == "X-User-Id header is required"


def test_user_sees_only_own_tasks(client):
    client.post(
        "/tasks",
        headers={"X-User-Id": "10"},
        json={"title": "Task 1", "description": None, "status": "todo", "priority": 1},
    )
    client.post(
        "/tasks",
        headers={"X-User-Id": "20"},
        json={"title": "Task 2", "description": None, "status": "done", "priority": 5},
    )

    response = client.get("/tasks", headers={"X-User-Id": "10"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "title": "Task 1",
            "description": None,
            "status": "todo",
            "priority": 1,
            "owner_id": 10,
        }
    ]


def test_tasks_filtering_by_status_and_priority(client):
    headers = {"X-User-Id": "10"}
    payloads = [
        {"title": "Low", "description": None, "status": "todo", "priority": 1},
        {"title": "Mid", "description": None, "status": "in_progress", "priority": 3},
        {"title": "High", "description": None, "status": "done", "priority": 5},
    ]
    for payload in payloads:
        client.post("/tasks", headers=headers, json=payload)

    response = client.get("/tasks?min_priority=3&status=done", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "High"


def test_update_status_success(client):
    client.post(
        "/tasks",
        headers={"X-User-Id": "10"},
        json={"title": "Task 123", "description": None, "status": "todo", "priority": 2},
    )

    response = client.patch(
        "/tasks/1/status",
        headers={"X-User-Id": "10"},
        json={"status": "done"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_foreign_or_missing_task_returns_404(client):
    client.post(
        "/tasks",
        headers={"X-User-Id": "10"},
        json={"title": "Task 123", "description": None, "status": "todo", "priority": 2},
    )

    foreign_response = client.get("/tasks/1", headers={"X-User-Id": "20"})
    missing_response = client.get("/tasks/999", headers={"X-User-Id": "10"})

    assert foreign_response.status_code == 404
    assert missing_response.status_code == 404


def test_delete_task_success(client):
    client.post(
        "/tasks",
        headers={"X-User-Id": "10"},
        json={"title": "Task 123", "description": None, "status": "todo", "priority": 2},
    )

    delete_response = client.delete("/tasks/1", headers={"X-User-Id": "10"})
    get_response = client.get("/tasks/1", headers={"X-User-Id": "10"})

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_healthcheck(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "env": "local"}

