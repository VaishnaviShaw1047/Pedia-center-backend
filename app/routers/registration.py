"""Registration route. HTTP only."""

from fastapi import APIRouter, status

from app import schemas
from app.service.service import RegistrationService

router = APIRouter()


@router.post(
    "/registration",
    response_model=schemas.RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_guardian(
    payload: schemas.RegistrationRequest,
):
    guardian, patients = RegistrationService.register(payload)

    return schemas.RegistrationResponse(
        guardian_id=guardian["guardian_id"],
        patients=[
            schemas.RegisteredPatientResponse.model_validate(patient)
            for patient in patients
        ],
        message="Registration successful",
    )