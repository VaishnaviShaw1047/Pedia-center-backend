"""Patient routes. HTTP only."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.service import PatientService

router = APIRouter()


def to_list_item(patient: models.Patient) -> schemas.PatientSummaryResponse:
    return schemas.PatientSummaryResponse(
        patient_id=patient.patient_id,
        mrn=patient.mrn,
        first_name=patient.first_name,
        last_name=patient.last_name,
        date_of_birth=patient.date_of_birth,
        gender=patient.gender,
        blood_group=patient.blood_group,
        guardian_name=f"{patient.guardian.first_name} {patient.guardian.last_name}",
        guardian_mobile=patient.guardian.mobile_number,
    )


@router.get("/patients", response_model=schemas.PatientListResponse)
def list_patients(
    search: str | None = Query(None, description="Name, MRN or guardian mobile"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total, patients = PatientService.list_patients(db, search, page, page_size)

    return schemas.PatientListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[to_list_item(p) for p in patients],
    )


@router.get("/patients/{mrn}", response_model=schemas.PatientDetailResponse)
def get_patient(mrn: str, db: Session = Depends(get_db)):
    return PatientService.get_by_mrn(db, mrn)


@router.patch("/patients/{mrn}", response_model=schemas.PatientDetailResponse)
def update_patient(
    mrn: str,
    payload: schemas.PatientUpdateRequest,
    db: Session = Depends(get_db),
):
    return PatientService.update(db, mrn, payload)

