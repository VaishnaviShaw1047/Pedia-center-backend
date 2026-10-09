"""
Router layer — HTTP only.

Declares the route, pulls dependencies, calls the service, shapes the
response. No queries, no business rules.
"""

from fastapi import APIRouter, Depends, Query, status

from app import schemas
from app.auth import get_current_user
from app.service.service import AuthService

router = APIRouter()


def to_out(appointment: dict) -> schemas.AppointmentResponse:
    """
    MongoDB appointment document -> response schema.

    Related doctor and patient information is populated by the
    AppointmentRepository.
    """

    return schemas.AppointmentResponse(
        appointment_id=appointment["appointment_id"],
        appointment_ref=appointment["appointment_ref"],
        doctor_id=appointment["doctor_id"],
        doctor_name=appointment["doctor_name"],
        patient_id=appointment["patient_id"],
        patient_name=appointment["patient_name"],
        mrn=appointment["mrn"],
        scheduled_at=appointment["scheduled_at"],
        duration_minutes=appointment["duration_minutes"],
        status=appointment["status"],
        reason_for_visit=appointment["reason_for_visit"],
    )


# =====================================================================
# BOOK APPOINTMENT
# =====================================================================

@router.post(
    "/appointments",
    response_model=schemas.AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def book_appointment(
    payload: schemas.AppointmentBookingRequest,
    current_user=Depends(get_current_user),
):
    appointment = AppointmentService.book(
        guardian=current_user,
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id,
        scheduled_at=payload.scheduled_at,
        reason_for_visit=payload.reason_for_visit,
    )

    return to_out(appointment)


# =====================================================================
# LIST APPOINTMENTS
# =====================================================================

@router.get(
    "/appointments",
    response_model=list[schemas.AppointmentResponse],
)
def my_appointments(
    upcoming_only: bool = Query(True),
    current_user=Depends(get_current_user),
):
    appointments = AppointmentService.list_for_guardian(
        guardian=current_user,
        upcoming_only=upcoming_only,
    )

    return [to_out(appointment) for appointment in appointments]


# =====================================================================
# CANCEL APPOINTMENT
# =====================================================================

@router.patch(
    "/appointments/{ref}/cancel",
    response_model=schemas.AppointmentResponse,
)
def cancel_appointment(
    ref: str,
    payload: schemas.AppointmentCancelRequest,
    current_user=Depends(get_current_user),
):
    appointment = AppointmentService.cancel(
        guardian=current_user,
        ref=ref,
    )

    return to_out(appointment)