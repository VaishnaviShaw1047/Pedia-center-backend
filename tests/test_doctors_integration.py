import time
from datetime import date, timedelta

from fastapi.testclient import TestClient

from main import app
from app import models
from app.auth import create_access_token
from app.database import DbSessionContext

client = TestClient(app)


def create_staff_token():
    """
    Create a temporary staff guardian directly in the test database
    and generate a real staff JWT.
    """

    db = DbSessionContext()

    try:
        mobile_number = f"9{int(time.time() * 1000) % 1_000_000_000:09d}"

        staff = models.Guardian(
            first_name="Test",
            last_name="Staff",
            relationship_to_child="Staff",
            mobile_number=mobile_number,
            email=f"staff{int(time.time() * 1000)}@example.com",
            password_hash="test-password-hash",
            role="staff",
            address_line1="123 Test Street",
            city="Kolkata",
            state="West Bengal",
            pincode="700001",
            preferred_language="English",
            terms_accepted=True,
            health_data_consent=True,
            mobile_verified=True,
            is_active=True,
        )

        db.add(staff)
        db.commit()
        db.refresh(staff)

        token = create_access_token(
            subject_id=staff.guardian_id,
            role=staff.role,
        )

        return token

    finally:
        db.close()


def create_guardian_token():
    """
    Create a normal guardian through the real registration API
    and login to obtain a JWT.
    """

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
                    "gender": "Male",
                }
            ],
        },
    )

    assert registration_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "mobile_number": mobile_number,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_doctor_integration_flow():
    """
    End-to-end integration test for doctor APIs.

    Covers:
    1. Public doctor list
    2. Staff authentication
    3. Doctor creation
    4. Guardian authentication
    5. Doctor browsing
    6. Doctor details
    7. Specialties
    8. Doctor availability creation
    9. Doctor availability listing
    10. Available slots
    """

    # ---------------------------------------------------------
    # 1. Public doctor list
    # ---------------------------------------------------------

    response = client.get("/api/v1/doctors")

    print("PUBLIC DOCTOR LIST:", response.status_code)
    print(response.json())

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # ---------------------------------------------------------
    # 2. Create staff token
    # ---------------------------------------------------------

    staff_token = create_staff_token()

    staff_headers = {
        "Authorization": f"Bearer {staff_token}"
    }

    # ---------------------------------------------------------
    # 3. Create doctor
    # ---------------------------------------------------------

    unique_id = int(time.time() * 1000)

    doctor_payload = {
        "first_name": "Test",
        "last_name": "Doctor",
        "registration_no": f"REG-{unique_id}",
        "qualification": "MBBS",
        "specialty": "Pediatrics",
        "experience_years": 5,
        "languages": "English, Hindi",
        "consultation_fee": 500,
        "available_days": "Mon,Wed,Fri",
        "mobile_number": f"9{unique_id % 1_000_000_000:09d}",
        "email": f"doctor{unique_id}@example.com",
        "temporary_password": "DoctorPass123",
    }

    response = client.post(
        "/api/v1/doctors",
        headers=staff_headers,
        json=doctor_payload,
    )

    print("CREATE DOCTOR:", response.status_code)
    print(response.json())

    assert response.status_code == 201

    doctor_data = response.json()

    assert "doctor_id" in doctor_data
    assert "staff_id" in doctor_data
    assert doctor_data["first_name"] == "Test"
    assert doctor_data["last_name"] == "Doctor"
    assert doctor_data["specialty"] == "Pediatrics"

    doctor_id = doctor_data["doctor_id"]

    # ---------------------------------------------------------
    # 4. Create normal guardian token
    # ---------------------------------------------------------

    guardian_token = create_guardian_token()

    guardian_headers = {
        "Authorization": f"Bearer {guardian_token}"
    }

    # ---------------------------------------------------------
    # 5. Browse available doctors
    # ---------------------------------------------------------

    response = client.get(
        "/api/v1/doctors/available",
        headers=guardian_headers,
    )

    print("AVAILABLE DOCTORS:", response.status_code)
    print(response.json())

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # ---------------------------------------------------------
    # 6. Get doctor by ID
    # ---------------------------------------------------------

    response = client.get(
        f"/api/v1/doctors/{doctor_id}",
        headers=guardian_headers,
    )

    print("GET DOCTOR:", response.status_code)
    print(response.json())

    assert response.status_code == 200

    doctor = response.json()

    assert doctor["doctor_id"] == doctor_id
    assert doctor["first_name"] == "Test"
    assert doctor["specialty"] == "Pediatrics"

    # ---------------------------------------------------------
    # 7. List specialties
    # ---------------------------------------------------------

    response = client.get(
        "/api/v1/doctors/specialties",
        headers=guardian_headers,
    )

    print("SPECIALTIES:", response.status_code)
    print(response.json())

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # ---------------------------------------------------------
    # 8. Create doctor availability
    # ---------------------------------------------------------

    tomorrow = date.today() + timedelta(days=1)

    availability_payload = {
        "day_of_week": tomorrow.weekday(),
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "slot_minutes": 30,
    }

    response = client.post(
        f"/api/v1/doctors/{doctor_id}/availability",
        headers=staff_headers,
        json=availability_payload,
    )

    print("CREATE AVAILABILITY:", response.status_code)
    print(response.json())

    assert response.status_code == 201

    availability = response.json()

    assert availability["doctor_id"] == doctor_id
    assert availability["day_of_week"] == tomorrow.weekday()
    assert availability["slot_minutes"] == 30

    # ---------------------------------------------------------
    # 9. List doctor availability
    # ---------------------------------------------------------

    response = client.get(
        f"/api/v1/doctors/{doctor_id}/availability",
        headers=guardian_headers,
    )

    print("DOCTOR AVAILABILITY:", response.status_code)
    print(response.json())

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

    # ---------------------------------------------------------
    # 10. Get available slots
    # ---------------------------------------------------------

    response = client.get(
        f"/api/v1/doctors/{doctor_id}/slots",
        params={"date": tomorrow.isoformat()},
        headers=guardian_headers,
    )

    print("AVAILABLE SLOTS:", response.status_code)
    print(response.json())

    assert response.status_code == 200

    slots_data = response.json()

    assert slots_data["doctor_id"] == doctor_id
    assert slots_data["date"] == tomorrow.isoformat()
    assert slots_data["day_of_week"] == tomorrow.weekday()
    assert isinstance(slots_data["slots"], list)
