import os
import time

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_create_20_doctors():

    # ============================================================
    # ADMIN LOGIN
    # ============================================================

    admin_username = os.getenv("TEST_ADMIN_USERNAME")
    admin_password = os.getenv("TEST_ADMIN_PASSWORD")

    assert admin_username, "TEST_ADMIN_USERNAME is not set"
    assert admin_password, "TEST_ADMIN_PASSWORD is not set"

    login_response = client.post(
        "/api/v1/auth/admin-login",
        json={
            "username": admin_username,
            "password": admin_password,
        },
    )

    print(
        "ADMIN LOGIN STATUS:",
        login_response.status_code,
    )

    print(
        "ADMIN LOGIN RESPONSE:",
        login_response.json(),
    )

    assert login_response.status_code == 200

    login_data = login_response.json()

    assert "access_token" in login_data

    admin_token = login_data["access_token"]

    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    # ============================================================
    # CREATE 20 DOCTORS
    # ============================================================

    created_doctors = []

    unique_value = int(time.time() * 1000)

    for i in range(1, 21):

        doctor_payload = {
            "first_name": f"TestDoctor{i}",
            "last_name": "Bulk",

            "registration_no":
                f"TEST-REG-{unique_value}-{i}",

            "qualification": "MBBS",

            "specialty": "Pediatrics",

            "experience_years": 5,

            "languages": "English, Hindi",

            "consultation_fee": 500,

            "available_days":
                "Monday,Tuesday,Wednesday,Thursday,Friday",

            "mobile_number":
                f"9{(unique_value + i) % 1_000_000_000:09d}",

            "email":
                f"testdoctor{i}_{unique_value}@example.com",

            "temporary_password":
                "DoctorTest@123",
        }

        response = client.post(
            "/api/v1/doctors",
            headers=admin_headers,
            json=doctor_payload,
        )

        print(
            f"DOCTOR {i} STATUS:",
            response.status_code,
        )

        print(
            f"DOCTOR {i} RESPONSE:",
            response.json(),
        )

        # --------------------------------------------------------
        # Verify doctor was created
        # --------------------------------------------------------

        assert response.status_code == 201, (
            f"Doctor {i} creation failed. "
            f"Status: {response.status_code}. "
            f"Response: {response.text}"
        )

        data = response.json()

        assert "doctor_id" in data
        assert "staff_id" in data

        created_doctors.append(
            {
                "doctor_id": data["doctor_id"],
                "staff_id": data["staff_id"],
                "email": doctor_payload["email"],
            }
        )

    # ============================================================
    # FINAL VALIDATION
    # ============================================================

    assert len(created_doctors) == 20

    # Every doctor must have a unique doctor_id
    doctor_ids = [
        doctor["doctor_id"]
        for doctor in created_doctors
    ]

    assert len(set(doctor_ids)) == 20

    # Every doctor must have a unique staff_id
    staff_ids = [
        doctor["staff_id"]
        for doctor in created_doctors
    ]

    assert len(set(staff_ids)) == 20

    print("\n========================================")
    print("20 DOCTORS CREATED SUCCESSFULLY")
    print("========================================")

    print("Doctor IDs:")
    print(doctor_ids)

    print("Staff IDs:")
    print(staff_ids)