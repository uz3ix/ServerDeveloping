import pytest
from fastapi.testclient import TestClient

from main import app, reset_users_state


@pytest.fixture(autouse=True)
def clean_users_state():
    reset_users_state()
    yield
    reset_users_state()


@pytest.fixture
def client():
    return TestClient(app)
