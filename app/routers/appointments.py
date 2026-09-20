"""
Router layer — HTTP only.

Declares the route, pulls dependencies, calls the service, shapes the
response. No queries, no rules. Compare this to the 130-line version
before the refactor.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.service import AppointmentService

router = APIRouter()


def to_out(appointment: models.Appointment) -> schemas.AppointmentResponse:
    """Model object -> response schema. Presentation, so it belongs here."""
    return schemas.AppointmentResponse(
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


@router.post(
    "/appointments",
    response_model=schemas.AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def book_appointment(
    payload: schemas.AppointmentBookingRequest,
    db: Session = Depends(get_db),
    current_user: models.Guardian = Depends(get_current_user),
):
    appointment = AppointmentService.book(
        db=db,
        guardian=current_user,
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id,
        scheduled_at=payload.scheduled_at,
        reason_for_visit=payload.reason_for_visit,
    )
    return to_out(appointment)


@router.get("/appointments", response_model=list[schemas.AppointmentResponse])
def my_appointments(
    upcoming_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: models.Guardian = Depends(get_current_user),
):
    appointments = AppointmentService.list_for_guardian(
        db=db, guardian=current_user, upcoming_only=upcoming_only
    )
    return [to_out(a) for a in appointments]


@router.patch("/appointments/{ref}/cancel", response_model=schemas.AppointmentResponse)
def cancel_appointment(
    ref: str,
    payload: schemas.AppointmentCancelRequest,
    db: Session = Depends(get_db),
    current_user: models.Guardian = Depends(get_current_user),
):
    appointment = AppointmentService.cancel(db=db, guardian=current_user, ref=ref)
    return to_out(appointment)

