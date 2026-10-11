from datetime import datetime, timezone

from fastapi import HTTPException

from app.repository import (
    DoctorAssignmentRepository,
    DoctorRepository,
    PatientRepository,
)


class DoctorAssignmentService:

    @classmethod
    def assign_doctor(cls, patient_id: int, doctor_id: int) -> dict:
        # 1. Validate the patient
        patient = PatientRepository.get_by_id(patient_id)

        if not patient or not patient.get("is_active", True):
            raise HTTPException(
                status_code=404,
                detail="Active patient not found",
            )

        # 2. Validate the doctor
        doctor = DoctorRepository.get_active_by_id(doctor_id)

        if not doctor:
            raise HTTPException(
                status_code=404,
                detail="Active doctor not found",
            )

        # 3. Prepare names
        patient_name = (
            f'{patient.get("first_name", "")} '
            f'{patient.get("last_name", "")}'
        ).strip()

        doctor_name = (
            f'{doctor.get("first_name", "")} '
            f'{doctor.get("last_name", "")}'
        ).strip()

        # 4. Create a new assignment history record
        assignment_date = datetime.now(timezone.utc)

        assignment = {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "assignment_date": assignment_date,
        }

        # 5. Save assignment history in MongoDB
        DoctorAssignmentRepository.add(assignment)

        # 6. Return the response
        return {
            "message": "Doctor assigned successfully",
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "assignment_date": assignment_date,
        }