def test_custom_exception_a_returns_consistent_error(client):
    response = client.get("/custom/a/-1")

    assert response.status_code == 400
    assert response.json() == {
        "error_code": "CUSTOM_A",
        "message": "Value must be greater than or equal to zero",
        "details": None,
    }


def test_custom_exception_b_returns_not_found(client):
    response = client.get("/custom/b/404")

    assert response.status_code == 404
    assert response.json()["error_code"] == "CUSTOM_B"
    assert response.json()["message"] == "Resource 404 not found"


def test_validate_user_accepts_valid_payload(client):
    payload = {
        "username": "alice",
        "age": 21,
        "email": "alice@example.com",
        "password": "secret123",
    }

    response = client.post("/validate-user", json=payload)

    assert response.status_code == 200
    assert response.json()["phone"] == "Unknown"


def test_validate_user_returns_custom_validation_error(client):
    payload = {
        "username": "bob",
        "age": 18,
        "email": "not-an-email",
        "password": "short",
    }

    response = client.post("/validate-user", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["message"] == "Request validation failed"
    assert len(body["details"]) >= 3


def test_user_crud_sync_flow(client):
    create_response = client.post("/users", json={"username": "john", "age": 30})

    assert create_response.status_code == 201
    user = create_response.json()
    assert user == {"id": 1, "username": "john", "age": 30}

    get_response = client.get("/users/1")
    assert get_response.status_code == 200
    assert get_response.json() == user

    delete_response = client.delete("/users/1")
    assert delete_response.status_code == 204
    assert delete_response.content == b""

    missing_response = client.get("/users/1")
    assert missing_response.status_code == 404
