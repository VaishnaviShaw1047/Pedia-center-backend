


from fastapi.testclient import TestClient
from main import app
from app.auth import verify_token
import time

client = TestClient(app)


def test_create_20_doctors():
    admin_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDAwMDAwMSIsInJvbGUiOiJBZG1pbiIsInR5cGUiOiJhZG1pbiIsImV4cCI6MTc5MTU1ODI2Mn0.qIBpd5bXN2c5HeXGPyWi2FoQmNgQLA_SLeF_AFdvKm4"

    # Temporary JWT diagnostic
    try:
        payload = verify_token(admin_token)
        print("JWT decoded successfully")
        print("Token type:", payload.get("type"))
        print("Token role:", payload.get("role"))
        print("Token subject:", payload.get("sub"))
    except Exception as exc:
        print("JWT validation failed:", type(exc).__name__, str(exc))
        raise

    headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    unique = int(time.time())

    doctor_names = [
        ("Aarav", "Mehta"),
        ("Rohan", "Kapoor"),
        ("Arjun", "Malhotra"),
        ("Vikram", "Sharma"),
        ("Rahul", "Verma"),
        ("Aditya", "Chatterjee"),
        ("Karan", "Bose"),
        ("Ankit", "Agarwal"),
        ("Siddharth", "Roy"),
        ("Nikhil", "Gupta"),
        ("Rajiv", "Banerjee"),
        ("Abhishek", "Das"),
        ("Saurabh", "Mukherjee"),
        ("Amit", "Sen"),
        ("Varun", "Sinha"),
        ("Manish", "Jain"),
        ("Akash", "Patel"),
        ("Pranav", "Iyer"),
        ("Rajat", "Deshmukh"),
        ("Dev", "Choudhary"),
    ]

    for i, (first_name, last_name) in enumerate(doctor_names, start=1):
        response = client.post(
            "/api/v1/doctors",
            headers=headers,
            json={
                "first_name": first_name,
                "last_name": last_name,
                "registration_no": f"TEST-{unique}-{i}",
                "qualification": "MBBS",
                "specialty": "Pediatrics",
                "experience_years": 5,
                "languages": "English, Hindi",
                "consultation_fee": 500,
                "available_days": (
                    "Monday,Tuesday,Wednesday,Thursday,Friday"
                ),
                "mobile_number": f"9{(unique + i) % 1000000000:09d}",
                "email": (
                    f"{first_name.lower()}.{last_name.lower()}"
                    f"{unique}@gmail.com"
                ),
                "temporary_password": "DoctorTest@123",
            },
        )

        print(i, response.status_code, response.json())
        assert response.status_code == 201, (
            f"Failed to create {first_name} {last_name}: "
            f"{response.status_code} - {response.text}"
        )