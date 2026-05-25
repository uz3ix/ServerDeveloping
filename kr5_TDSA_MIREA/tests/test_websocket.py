from starlette.websockets import WebSocketDisconnect


def test_connect_with_valid_username(client):
    with client.websocket_connect("/ws/rooms/python?username=alice") as websocket:
        event = websocket.receive_json()

    assert event == {"type": "join", "room_id": "python", "username": "alice"}


def test_send_message_and_receive_broadcast(client):
    with client.websocket_connect("/ws/rooms/python?username=alice") as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "message", "text": "Всем привет"})
        response = websocket.receive_json()

    assert response == {
        "type": "message",
        "room_id": "python",
        "username": "alice",
        "text": "Всем привет",
    }


def test_two_clients_in_same_room_receive_same_message(client):
    with client.websocket_connect("/ws/rooms/python?username=alice") as alice:
        alice.receive_json()
        with client.websocket_connect("/ws/rooms/python?username=bob") as bob:
            bob_join = bob.receive_json()
            alice_join = alice.receive_json()

            assert bob_join == {"type": "join", "room_id": "python", "username": "bob"}
            assert alice_join == {"type": "join", "room_id": "python", "username": "bob"}

            alice.send_json({"type": "message", "text": "hello room"})
            alice_message = alice.receive_json()
            bob_message = bob.receive_json()

    expected = {
        "type": "message",
        "room_id": "python",
        "username": "alice",
        "text": "hello room",
    }
    assert alice_message == expected
    assert bob_message == expected


def test_different_rooms_do_not_receive_foreign_messages(client):
    with client.websocket_connect("/ws/rooms/python?username=alice") as alice:
        alice.receive_json()
        with client.websocket_connect("/ws/rooms/fastapi?username=bob") as bob:
            bob.receive_json()
            alice.send_json({"type": "message", "text": "isolated"})
            response = alice.receive_json()

            assert response["room_id"] == "python"
            assert response["text"] == "isolated"
            users_response = client.get("/rooms/fastapi/users")
            assert users_response.json() == {"room_id": "fastapi", "users": ["bob"]}


def test_too_long_message_returns_error(client):
    with client.websocket_connect("/ws/rooms/python?username=alice") as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "message", "text": "a" * 301})
        response = websocket.receive_json()

    assert response == {"type": "error", "detail": "Message is too long"}


def test_disconnected_user_removed_from_room(client):
    with client.websocket_connect("/ws/rooms/python?username=alice") as websocket:
        websocket.receive_json()
        response = client.get("/rooms/python/users")
        assert response.json() == {"room_id": "python", "users": ["alice"]}

    response_after_disconnect = client.get("/rooms/python/users")

    assert response_after_disconnect.json() == {"room_id": "python", "users": []}


def test_blank_username_is_rejected(client):
    try:
        with client.websocket_connect("/ws/rooms/python?username=%20%20") as websocket:
            websocket.receive_json()
    except WebSocketDisconnect as exc:
        assert exc.code == 1008
    else:
        raise AssertionError("WebSocket connection should be rejected")

