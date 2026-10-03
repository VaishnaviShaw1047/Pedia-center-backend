import time

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_registration_and_login_integration():
    mobile_number = f"9{int(time.time() * 1000) % 1_000_000_000:09d}"
    password = "TestPassword123"

    registration_response = client.post(
        "/api/v1/registration",
        json={
            "first_name": "Test",
            "last_name": "Guardian",
            "relationship_to_child": "Mother",
            "mobile_number": mobile_number,
            "password": password,
            "address_line1": "123 Test Street",
            "city": "Kolkata",
            "state": "West Bengal",
            "pincode": "700001",
            "preferred_language": "English",
            "terms_accepted": True,
            "health_data_consent": True,
            "children": [
                {
                    "first_name": "Test",
                    "last_name": "Child",
                    "date_of_birth": "2015-01-15",
                    "gender": "Male"
                }
            ]
        }
    )

    print("REGISTRATION STATUS:", registration_response.status_code)
    print("REGISTRATION RESPONSE:", registration_response.json())

    assert registration_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "mobile_number": mobile_number,
            "password": password
        }
    )

    print("LOGIN STATUS:", login_response.status_code)
    print("LOGIN RESPONSE:", login_response.json())

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert data["access_token"]