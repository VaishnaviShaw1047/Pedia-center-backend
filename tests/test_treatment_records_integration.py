from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_create_400_treatment_records():

    # Existing patient and doctor from the database
    patient_id = 1
    doctor_id = 1

    # Valid Admin JWT
    admin_token = "YOUR_ADMIN_ACCESS_TOKEN"

    headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    created_record_ids = []

    # ---------------------------------------------------------
    # Create 400 treatment records
    # ---------------------------------------------------------

    for i in range(1, 401):

        visit_date = datetime.utcnow() - timedelta(days=i)

        response = client.post(
            "/api/v1/treatment-records",
            headers=headers,
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "appointment_id": None,

                "visit_date": visit_date.isoformat(),

                "diagnosis": f"Integration Test Diagnosis {i}",

                "medications": [
                    {
                        "medication_name": f"Test Medicine {i}",
                        "dosage": "10 mg",
                        "frequency": "Once daily",
                        "duration": "5 days",
                        "instructions": "Take after food"
                    }
                ],

                "treatment_plan": (
                    f"Integration test treatment plan {i}"
                ),

                "follow_up_date": (
                    visit_date + timedelta(days=7)
                ).isoformat(),

                "clinical_notes": (
                    f"Integration test clinical notes {i}"
                )
            }
        )

        # -----------------------------------------------------
        # Verify API response
        # -----------------------------------------------------

        assert response.status_code == 200, (
            f"Failed to create treatment record {i}. "
            f"Status: {response.status_code}. "
            f"Response: {response.text}"
        )

        data = response.json()

        # -----------------------------------------------------
        # Verify response fields
        # -----------------------------------------------------

        assert "treatment_record_id" in data

        assert data["patient_id"] == patient_id

        assert data["doctor_id"] == doctor_id

        assert data["diagnosis"] == (
            f"Integration Test Diagnosis {i}"
        )

        assert data["record_status"] == "active"

        created_record_ids.append(
            data["treatment_record_id"]
        )

    # ---------------------------------------------------------
    # Verify exactly 400 records were created
    # ---------------------------------------------------------

    assert len(created_record_ids) == 400

    # Every record should have a unique ID
    assert len(set(created_record_ids)) == 400

    print(
        f"\nSuccessfully created "
        f"{len(created_record_ids)} treatment records."
    )