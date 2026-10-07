import time
from datetime import date, timedelta

from fastapi.testclient import TestClient

from main import app
from app.auth import create_access_token, hash_password
from app.mongodb import guardians_collection


client = TestClient(app)


def create_staff_token():
    """
    Create a temporary staff guardian directly in MongoDB
    and generate a real staff JWT.
    """

    last_guardian = guardians_collection.find_one(
        {},
        sort=[("guardian_id", -1)],
    )

    guardian_id = (
        last_guardian["guardian_id"] + 1
        if last_guardian
        else 1
    )

    unique_id = int(time.time() * 1000)

    mobile_number = (
        f"9{unique_id % 1_000_000_000:09d}"
    )

    staff = {
        "guardian_id": guardian_id,
        "first_name": "Test",
        "last_name": "Staff",
        "relationship_to_child": "Staff",
        "mobile_number": mobile_number,
        "email": f"staff{unique_id}@example.com",
        "password_hash": hash_password(
            "TestStaffPassword123"
        ),
        "role": "staff",
        "address_line1": "123 Test Street",
        "city": "Kolkata",
        "state": "West Bengal",
        "pincode": "700001",
        "preferred_language": "English",
        "terms_accepted": True,
        "health_data_consent": True,
        "mobile_verified": True,
        "is_active": True,
    }

    guardians_collection.insert_one(staff)

    return create_access_token(
        subject_id=guardian_id,
        role="staff",
    )


def create_guardian_token():
    """
    Create a guardian and patient through the real
    registration API, then login through the real auth API.
    """

    unique_id = int(time.time() * 1000)

    mobile_number = (
        f"9{unique_id % 1_000_000_000:09d}"
    )

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

    print(
        "REGISTRATION:",
        registration_response.status_code,
    )
    print(registration_response.json())

    assert registration_response.status_code == 201

    registration_data = registration_response.json()

    patient_id = registration_data["patients"][0][
        "patient_id"
    ]

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "mobile_number": mobile_number,
            "password": password,
        },
    )

    print(
        "GUARDIAN LOGIN:",
        login_response.status_code,
    )
    print(login_response.json())

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return token, patient_id


def test_appointment_integration_flow():

    # ================================================================
    # 1. Create guardian and patient
    # ================================================================

    guardian_token, patient_id = create_guardian_token()

    guardian_headers = {
        "Authorization": f"Bearer {guardian_token}"
    }

    print("PATIENT ID:", patient_id)

    # ================================================================
    # 2. Create staff token
    # ================================================================

    staff_token = create_staff_token()

    staff_headers = {
        "Authorization": f"Bearer {staff_token}"
    }

    # ================================================================
    # 3. Create doctor
    # ================================================================

    unique_id = int(time.time() * 1000)

    doctor_payload = {
        "first_name": "Test",
        "last_name": "AppointmentDoctor",
        "registration_no": f"REG-APT-{unique_id}",
        "qualification": "MBBS",
        "specialty": "Pediatrics",
        "experience_years": 5,
        "languages": "English, Hindi",
        "consultation_fee": 500,
        "available_days": "Sun",
        "mobile_number": (
            f"9{unique_id % 1_000_000_000:09d}"
        ),
        "email": (
            f"appointmentdoctor{unique_id}@example.com"
        ),
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

    doctor_id = doctor_data["doctor_id"]

    assert "doctor_id" in doctor_data
    assert "staff_id" in doctor_data
    assert doctor_data["first_name"] == "Test"
    assert doctor_data["last_name"] == "AppointmentDoctor"
    assert doctor_data["specialty"] == "Pediatrics"

    # ================================================================
    # 4. Create doctor availability for tomorrow
    # ================================================================

    appointment_date = date.today() + timedelta(days=1)

    availability_payload = {
        "day_of_week": appointment_date.weekday(),
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "slot_minutes": 30,
    }

    response = client.post(
        f"/api/v1/doctors/{doctor_id}/availability",
        headers=staff_headers,
        json=availability_payload,
    )

    print(
        "CREATE AVAILABILITY:",
        response.status_code,
    )
    print(response.json())

    assert response.status_code == 201

    availability = response.json()

    assert availability["doctor_id"] == doctor_id
    assert (
        availability["day_of_week"]
        == appointment_date.weekday()
    )
    assert availability["slot_minutes"] == 30

    # ================================================================
    # 5. Book appointment
    # ================================================================

    scheduled_at = (
        f"{appointment_date.isoformat()}T09:00:00"
    )

    appointment_payload = {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "scheduled_at": scheduled_at,
        "reason_for_visit": (
            "Routine pediatric consultation"
        ),
    }

    response = client.post(
        "/api/v1/appointments",
        headers=guardian_headers,
        json=appointment_payload,
    )

    print(
        "BOOK APPOINTMENT:",
        response.status_code,
    )
    print(response.json())

    assert response.status_code == 201

    appointment = response.json()

    assert "appointment_id" in appointment
    assert "appointment_ref" in appointment

    assert appointment["doctor_id"] == doctor_id
    assert appointment["patient_id"] == patient_id

    assert appointment["scheduled_at"].startswith(
        appointment_date.isoformat()
    )

    assert appointment["duration_minutes"] == 30
    assert appointment["status"] == "requested"

    assert (
        appointment["reason_for_visit"]
        == "Routine pediatric consultation"
    )

    appointment_ref = appointment[
        "appointment_ref"
    ]

    # ================================================================
    # 6. Get guardian's upcoming appointments
    # ================================================================

    response = client.get(
        "/api/v1/appointments",
        headers=guardian_headers,
    )

    print(
        "MY APPOINTMENTS:",
        response.status_code,
    )
    print(response.json())

    assert response.status_code == 200

    appointments = response.json()

    assert isinstance(
        appointments,
        list,
    )

    matching_appointment = next(
        (
            item
            for item in appointments
            if item["appointment_ref"]
            == appointment_ref
        ),
        None,
    )

    assert matching_appointment is not None

    assert (
        matching_appointment["doctor_id"]
        == doctor_id
    )

    assert (
        matching_appointment["patient_id"]
        == patient_id
    )

    assert (
        matching_appointment["status"]
        == "requested"
    )

    # ================================================================
    # 7. Cancel appointment
    # ================================================================

    response = client.patch(
        f"/api/v1/appointments/{appointment_ref}/cancel",
        headers=guardian_headers,
        json={
            "reason": "Patient is unavailable"
        },
    )

    print(
        "CANCEL APPOINTMENT:",
        response.status_code,
    )
    print(response.json())

    assert response.status_code == 200

    cancelled_appointment = response.json()

    assert (
        cancelled_appointment["appointment_ref"]
        == appointment_ref
    )

    assert (
        cancelled_appointment["status"]
        == "cancelled"
    )

    # ================================================================
    # 8. Verify cancellation
    # ================================================================

    response = client.get(
        "/api/v1/appointments?upcoming_only=false",
        headers=guardian_headers,
    )

    print(
        "ALL APPOINTMENTS AFTER CANCELLATION:",
        response.status_code,
    )
    print(response.json())

    assert response.status_code == 200

    appointments_after_cancel = response.json()

    cancelled = next(
        (
            item
            for item in appointments_after_cancel
            if item["appointment_ref"]
            == appointment_ref
        ),
        None,
    )

    assert cancelled is not None

    assert (
        cancelled["appointment_ref"]
        == appointment_ref
    )

    assert (
        cancelled["doctor_id"]
        == doctor_id
    )

    assert (
        cancelled["patient_id"]
        == patient_id
    )

    assert (
        cancelled["status"]
        == "cancelled"
    )