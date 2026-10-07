from fastapi import APIRouter, Depends

from app import schemas
from app.auth import (
    require_treatment_record_creator,
    require_treatment_record_viewer,
)
from app.service import TreatmentRecordService


router = APIRouter(
    prefix="/treatment-records",
)


# =====================================================================
# CREATE TREATMENT RECORD
# =====================================================================

@router.post(
    "",
    response_model=schemas.TreatmentRecordResponse,
)
def create_treatment_record(
    payload: schemas.TreatmentRecordCreateRequest,
    current_user=Depends(
        require_treatment_record_creator
    ),
):
    return TreatmentRecordService.create(
        payload,
        current_user,
    )


# =====================================================================
# GET PATIENT TREATMENT HISTORY
# =====================================================================

@router.get(
    "/{patient_id}",
    response_model=list[schemas.TreatmentRecordResponse],
)
def get_patient_treatment_history(
    patient_id: int,
    current_user=Depends(
        require_treatment_record_viewer
    ),
):
    return TreatmentRecordService.get_patient_history(
        patient_id,
        current_user,
    )


# =====================================================================
# GET LATEST PATIENT TREATMENT RECORD
# =====================================================================

@router.get(
    "/{patient_id}/latest",
    response_model=schemas.TreatmentRecordResponse,
)
def get_latest_patient_treatment_record(
    patient_id: int,
    current_user=Depends(
        require_treatment_record_viewer
    ),
):
    return TreatmentRecordService.get_latest_patient_record(
        patient_id,
        current_user,
    )


# =====================================================================
# GET DOCTOR TREATMENT RECORDS
# =====================================================================

@router.get(
    "/doctor/{doctor_id}",
    response_model=list[schemas.DoctorTreatmentSummaryResponse],
)
def get_doctor_treatment_records(
    doctor_id: int,
    current_user=Depends(
        require_treatment_record_viewer
    ),
):
    return TreatmentRecordService.get_doctor_records(
        doctor_id,
        current_user,
    )