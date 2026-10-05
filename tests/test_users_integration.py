from time import time

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_create_user():
    unique_id = int(time() * 1000)

    username = f"integration_user_{unique_id}"

    payload = {
        "username": username,
        "password": "Test@1234",
        "user_type": "Admin",
        "first_name": "Integration",
        "last_name": "User",
    }

    response = client.post(
        "/api/v1/users",
        json=payload,
    )

    print("\nCREATE USER RESPONSE:", response.status_code)
    print(response.json())

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == username
    assert data["user_type"] == "Admin"
    assert data["first_name"] == "Integration"
    assert data["last_name"] == "User"
    assert "user_id" in data