from fastapi.testclient import TestClient
from main import app
import time

client = TestClient(app)


def test_create_20_doctors():

    admin_token = "PASTE_YOUR_ADMIN_ACCESS_TOKEN_HERE"

    headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    unique = int(time.time())

    for i in range(1, 21):

        response = client.post(
            "/api/v1/doctors",
            headers=headers,
            json={
                "first_name": f"Sunil{i}",
                "last_name": "Shaw",
                "registration_no": f"TEST-{unique}-{i}",
                "qualification": "MBBS",
                "specialty": "Pediatrics",
                "experience_years": 5,
                "languages": "English, Hindi",
                "consultation_fee": 500,
                "available_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
                "mobile_number": f"900000{unique % 10000:04d}{i:02d}",
                "email": f"doctor{i}_{unique}@test.com",
                "temporary_password": "DoctorTest@123"
            }
        )

        print(i, response.status_code, response.json())

        assert response.status_code == 201