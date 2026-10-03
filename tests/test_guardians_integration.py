import time

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_guardian_registration_login_and_profile():
    """
    Integration test for Guardian APIs.

    Covers:
    1. Guardian registration
    2. Child registration under guardian
    3. Guardian login
    4. JWT authentication
    5. Guardian profile (/auth/me)
    """

    # ---------------------------------------------------------
    # 1. Create unique test guardian
    # ---------------------------------------------------------

    unique_id = int(time.time() * 1000)

    mobile_number = f"9{unique_id % 1_000_000_000:09d}"
    password = "TestPassword123"

    # ---------------------------------------------------------
    # 2. Guardian registration
    # ---------------------------------------------------------

    registration_payload = {
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
                "gender": "Male",
            }
        ],
    }

    response = client.post(
        "/api/v1/registration",
        json=registration_payload,
    )

    print("GUARDIAN REGISTRATION:", response.status_code)
    print(response.json())

    assert response.status_code == 201

    registration_data = response.json()

    assert "guardian_id" in registration_data
    assert "patients" in registration_data
    assert registration_data["message"] == "Registration successful"

    assert len(registration_data["patients"]) == 1

    patient = registration_data["patients"][0]

    assert "patient_id" in patient
    assert "mrn" in patient
    assert patient["first_name"] == "Test"

    guardian_id = registration_data["guardian_id"]

    # ---------------------------------------------------------
    # 3. Guardian login
    # ---------------------------------------------------------

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "mobile_number": mobile_number,
            "password": password,
        },
    )

    print("GUARDIAN LOGIN:", login_response.status_code)
    print(login_response.json())

    assert login_response.status_code == 200

    login_data = login_response.json()

    assert "access_token" in login_data
    assert login_data["access_token"]
    assert login_data["token_type"] == "bearer"

    access_token = login_data["access_token"]

    # ---------------------------------------------------------
    # 4. Access guardian profile
    # ---------------------------------------------------------

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    profile_response = client.get(
        "/api/v1/auth/me",
        headers=headers,
    )

    print("GUARDIAN PROFILE:", profile_response.status_code)
    print(profile_response.json())

    assert profile_response.status_code == 200

    profile = profile_response.json()

    # ---------------------------------------------------------
    # 5. Verify guardian profile
    # ---------------------------------------------------------

    assert profile["guardian_id"] == guardian_id
    assert profile["first_name"] == "Test"
    assert profile["last_name"] == "Guardian"
    assert profile["mobile_number"] == mobile_number
    assert profile["role"] == "parent"