from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import models, schemas
from datetime import date, datetime, time, timedelta
from app.auth import hash_password, require_staff, get_current_user
from app.database import get_db

router = APIRouter()


def generate_staff_id(doctor_id: int) -> str:
    return f"DOC-2026-{doctor_id:04d}"


@router.post(
    "/doctors",
    response_model=schemas.DoctorCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_doctor(
    payload: schemas.DoctorCreate,
    db: Session = Depends(get_db),
    _staff: models.Guardian = Depends(require_staff),
):
    existing = (
        db.query(models.Doctor)
        .filter(models.Doctor.registration_no == payload.registration_no)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A doctor with this registration number already exists",
        )

    doctor = models.Doctor(
        staff_id="",
        first_name=payload.first_name,
        last_name=payload.last_name,
        registration_no=payload.registration_no,
        qualification=payload.qualification,
        specialty=payload.specialty,
        experience_years=payload.experience_years,
        languages=payload.languages,
        consultation_fee=payload.consultation_fee,
        available_days=payload.available_days,
        mobile_number=payload.mobile_number,
        email=payload.email,
        password_hash=hash_password(payload.temporary_password),
    )

    db.add(doctor)
    db.flush()

    doctor.staff_id = generate_staff_id(doctor.doctor_id)
    db.commit()
    db.refresh(doctor)

    return schemas.DoctorCreated(
        doctor_id=doctor.doctor_id,
        staff_id=doctor.staff_id,
        first_name=doctor.first_name,
        last_name=doctor.last_name,
        specialty=doctor.specialty,
        message="Doctor created. Share the staff ID and temporary password securely.",
    )


@router.get("/doctors", response_model=list[schemas.DoctorListItem])
def list_doctors(
    specialty: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(models.Doctor).filter(models.Doctor.is_active == True)

    if specialty:
        query = query.filter(models.Doctor.specialty.ilike(f"%{specialty}%"))

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Doctor.first_name.ilike(term),
                models.Doctor.last_name.ilike(term),
                models.Doctor.specialty.ilike(term),
            )
        )

    return query.order_by(models.Doctor.first_name).all()