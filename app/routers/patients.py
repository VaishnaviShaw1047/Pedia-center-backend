"""Patient routes. HTTP only."""

from fastapi import APIRouter, Query

from app import schemas
from app.service.service import PatientService

router = APIRouter()


def to_list_item(patient: dict) -> schemas.PatientSummaryResponse:
    return schemas.PatientSummaryResponse(
        patient_id=patient["patient_id"],
        mrn=patient["mrn"],
        first_name=patient["first_name"],
        last_name=patient["last_name"],
        date_of_birth=patient["date_of_birth"],
        gender=patient["gender"],
        blood_group=patient.get("blood_group"),
        guardian_name=patient.get("guardian_name"),
        guardian_mobile=patient.get("guardian_mobile_number"),
    )


@router.get("/patients", response_model=schemas.PatientListResponse)
def list_patients(
    search: str | None = Query(
        None,
        description="Name, MRN or guardian mobile",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    total, patients = PatientService.list_patients(
        search,
        page,
        page_size,
    )

    return schemas.PatientListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[to_list_item(p) for p in patients],
    )


@router.get(
    "/patients/{mrn}",
    response_model=schemas.PatientDetailResponse,
)
def get_patient(mrn: str):
    return PatientService.get_by_mrn(mrn)


@router.patch(
    "/patients/{mrn}",
    response_model=schemas.PatientDetailResponse,
)
def update_patient(
    mrn: str,
    payload: schemas.PatientUpdateRequest,
):
    return PatientService.update(mrn, payload)