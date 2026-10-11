from fastapi import APIRouter, Depends

from app.auth import require_treatment_record_creator
from app.schemas import (
    PatientDoctorAssignmentRequest,
    PatientDoctorAssignmentResponse,
)
from app.service.doctor_assignment_service import DoctorAssignmentService

router = APIRouter(
    prefix="/doctor-assignments",
    tags=["Doctor Assignments"],
)


@router.post(
    "/",
    response_model=PatientDoctorAssignmentResponse,
)
def assign_doctor(
    request: PatientDoctorAssignmentRequest,
    current_user: dict = Depends(require_treatment_record_creator),
):
    return DoctorAssignmentService.assign_doctor(
        patient_id=request.patient_id,
        doctor_id=request.doctor_id,
    )
