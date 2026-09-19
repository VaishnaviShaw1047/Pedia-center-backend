from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter()


def generate_ref(appointment_id: int) -> str:
    return f"APT-2026-{appointment_id:06d}"


def to_out(appointment: models.Appointment) -> schemas.AppointmentOut:
    return schemas.AppointmentOut(
        appointment_id=appointment.appointment_id,
        appointment_ref=appointment.appointment_ref,
        doctor_id=appointment.doctor_id,
        doctor_name=f"{appointment.doctor.first_name} {appointment.doctor.last_name}",
        patient_id=appointment.patient_id,
        patient_name=f"{appointment.patient.first_name} {appointment.patient.last_name}",
        mrn=appointment.patient.mrn,
        scheduled_at=appointment.scheduled_at,
        duration_minutes=appointment.duration_minutes,
        status=appointment.status,
        reason_for_visit=appointment.reason_for_visit,
    )


def slot_is_offered(db: Session, doctor_id: int, when: datetime) -> int | None:
    """Return the slot length if the doctor offers this exact time, else None."""
    rules = (
        db.query(models.DoctorAvailability)
        .filter(
            models.DoctorAvailability.doctor_id == doctor_id,
            models.DoctorAvailability.day_of_week == when.weekday(),
            models.DoctorAvailability.is_active == True,
        )
        .all()
    )

    for rule in rules:
        cursor = datetime.combine(when.date(), rule.start_time)
        day_end = datetime.combine(when.date(), rule.end_time)
        step = timedelta(minutes=rule.slot_minutes)

        while cursor + step <= day_end:
            if cursor == when:
                return rule.slot_minutes
            cursor += step

    return None


@router.post(
    "/appointments",
    response_model=schemas.AppointmentOut,
    status_code=status.HTTP_201_CREATED,
)
def book_appointment(
    payload: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.Guardian = Depends(get_current_user),
):
    doctor = (
        db.query(models.Doctor)
        .filter(
            models.Doctor.doctor_id == payload.doctor_id,
            models.Doctor.is_active == True,
        )
        .first()
    )
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # ownership: the child must belong to the caller
    patient = (
        db.query(models.Patient)
        .filter(
            models.Patient.patient_id == payload.patient_id,
            models.Patient.guardian_id == current_user.guardian_id,
            models.Patient.is_active == True,
        )
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    when = payload.scheduled_at.replace(second=0, microsecond=0, tzinfo=None)

    if when <= datetime.now():
        raise HTTPException(
            status_code=400, detail="Appointment time must be in the future"
        )

    slot_minutes = slot_is_offered(db, doctor.doctor_id, when)
    if slot_minutes is None:
        raise HTTPException(
            status_code=400,
            detail="That time is not an available slot for this doctor",
        )

    taken = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.doctor_id == doctor.doctor_id,
            models.Appointment.scheduled_at == when,
            models.Appointment.status.in_(["requested", "confirmed"]),
        )
        .first()
    )
    if taken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That slot has just been taken",
        )

    day_start = datetime.combine(when.date(), time.min)
    day_end = datetime.combine(when.date(), time.max)

    same_day = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.patient_id == patient.patient_id,
            models.Appointment.scheduled_at >= day_start,
            models.Appointment.scheduled_at <= day_end,
            models.Appointment.status.in_(["requested", "confirmed"]),
        )
        .first()
    )
    if same_day:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This patient already has an appointment on that day",
        )

    appointment = models.Appointment(
        appointment_ref="",
        doctor_id=doctor.doctor_id,
        patient_id=patient.patient_id,
        guardian_id=current_user.guardian_id,
        scheduled_at=when,
        duration_minutes=slot_minutes,
        status="requested",
        reason_for_visit=payload.reason_for_visit,
    )

    db.add(appointment)

    try:
        db.flush()
        appointment.appointment_ref = generate_ref(appointment.appointment_id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That slot has just been taken",
        )

    db.refresh(appointment)
    return to_out(appointment)


@router.get("/appointments", response_model=list[schemas.AppointmentOut])
def my_appointments(
    upcoming_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: models.Guardian = Depends(get_current_user),
):
    query = (
        db.query(models.Appointment)
        .options(
            joinedload(models.Appointment.doctor),
            joinedload(models.Appointment.patient),
        )
        .filter(models.Appointment.guardian_id == current_user.guardian_id)
    )

    if upcoming_only:
        query = query.filter(
            models.Appointment.scheduled_at >= datetime.now(),
            models.Appointment.status.in_(["requested", "confirmed"]),
        )

    appointments = query.order_by(models.Appointment.scheduled_at).all()
    return [to_out(a) for a in appointments]


@router.patch("/appointments/{ref}/cancel", response_model=schemas.AppointmentOut)
def cancel_appointment(
    ref: str,
    payload: schemas.AppointmentCancel,
    db: Session = Depends(get_db),
    current_user: models.Guardian = Depends(get_current_user),
):
    appointment = (
        db.query(models.Appointment)
        .options(
            joinedload(models.Appointment.doctor),
            joinedload(models.Appointment.patient),
        )
        .filter(
            models.Appointment.appointment_ref == ref,
            models.Appointment.guardian_id == current_user.guardian_id,
        )
        .first()
    )

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status in ("cancelled", "completed"):
        raise HTTPException(
            status_code=400,
            detail=f"This appointment is already {appointment.status}",
        )

    appointment.status = "cancelled"
    db.commit()
    db.refresh(appointment)

    return to_out(appointment)