import pytest
from fastapi.testclient import TestClient

from app.main import app, reset_state


@pytest.fixture(autouse=True)
def clean_state():
    reset_state()
    yield
    reset_state()


@pytest.fixture
def client():
    return TestClient(app)

