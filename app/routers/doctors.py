"""
Doctor routes. HTTP only.

Route order matters: /doctors/available and /doctors/specialties are
declared BEFORE /doctors/{doctor_id}, or the path-parameter route would
swallow "available" and fail parsing it as an integer.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_staff
from app.database import get_db
from app.service import DoctorService

router = APIRouter()


# ---------- staff ----------

@router.post(
    "/doctors",
    response_model=schemas.DoctorCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_doctor(
    payload: schemas.DoctorCreateRequest,
    db: Session = Depends(get_db),
    _staff: models.Guardian = Depends(require_staff),
):
    doctor = DoctorService.create(db, payload)

    return schemas.DoctorCreateResponse(
        doctor_id=doctor.doctor_id,
        staff_id=doctor.staff_id,
        first_name=doctor.first_name,
        last_name=doctor.last_name,
        specialty=doctor.specialty,
        message="Doctor created. Share the staff ID and temporary password securely.",
    )


@router.post(
    "/doctors/{doctor_id}/availability",
    response_model=schemas.AvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
def set_availability(
    doctor_id: int,
    payload: schemas.AvailabilityCreateRequest,
    db: Session = Depends(get_db),
    _staff: models.Guardian = Depends(require_staff),
):
    return DoctorService.set_availability(db, doctor_id, payload)


# ---------- guardian facing ----------

@router.get("/doctors/available", response_model=list[schemas.DoctorPublicResponse])
def browse_doctors(
    specialty: str | None = Query(None),
    language: str | None = Query(None),
    max_fee: int | None = Query(None, ge=0),
    day: str | None = Query(None, description="e.g. Mon"),
    db: Session = Depends(get_db),
    _user: models.Guardian = Depends(get_current_user),
):
    return DoctorService.browse(db, specialty, language, max_fee, day)


@router.get("/doctors/specialties", response_model=list[schemas.SpecialtyCountResponse])
def list_specialties(
    db: Session = Depends(get_db),
    _user: models.Guardian = Depends(get_current_user),
):
    rows = DoctorService.specialties(db)
    return [
        schemas.SpecialtyCountResponse(specialty=r.specialty, doctor_count=r.doctor_count)
        for r in rows
    ]


@router.get("/doctors", response_model=list[schemas.DoctorSummaryResponse])
def list_doctors(
    specialty: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return DoctorService.browse(db, specialty=specialty, text=search)


@router.get("/doctors/{doctor_id}", response_model=schemas.DoctorPublicResponse)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    _user: models.Guardian = Depends(get_current_user),
):
    return DoctorService.get_one(db, doctor_id)


@router.get(
    "/doctors/{doctor_id}/availability",
    response_model=list[schemas.AvailabilityResponse],
)
def list_availability(
    doctor_id: int,
    db: Session = Depends(get_db),
    _user: models.Guardian = Depends(get_current_user),
):
    return DoctorService.list_availability(db, doctor_id)


@router.get("/doctors/{doctor_id}/slots", response_model=schemas.AvailableSlotsResponse)
def free_slots(
    doctor_id: int,
    slot_date: date = Query(..., alias="date", description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _user: models.Guardian = Depends(get_current_user),
):
    doctor, weekday, slots = DoctorService.free_slots(db, doctor_id, slot_date)

    return schemas.AvailableSlotsResponse(
        doctor_id=doctor.doctor_id,
        doctor_name=f"{doctor.first_name} {doctor.last_name}",
        date=slot_date,
        day_of_week=weekday,
        slots=slots,
    )

