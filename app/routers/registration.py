"""Registration route. HTTP only."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.service import RegistrationService

router = APIRouter()


@router.post(
    "/registration",
    response_model=schemas.RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_guardian(
    payload: schemas.RegistrationRequest,
    db: Session = Depends(get_db),
):
    guardian, patients = RegistrationService.register(db, payload)

    return schemas.RegistrationResponse(
        guardian_id=guardian.guardian_id,
        patients=[schemas.RegisteredPatientResponse.model_validate(p) for p in patients],
        message="Registration successful",
    )

