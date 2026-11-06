from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.auth import get_current_doctor
from app.repository.mongodb import (
    appointments_collection,
    doctor_assignments_collection,
    patients_collection,
)
from app.repository.repository import AppointmentRepository
from app.routers.appointments import to_out
from app.routers.patients import to_list_item
from app.schemas import schemas

router = APIRouter()


def _doctor_id(doctor) -> int:
    return doctor["doctor_id"] if isinstance(doctor, dict) else doctor.doctor_id


@router.get(
    "/doctor/appointments",
    response_model=list[schemas.AppointmentResponse],
)
def doctor_appointments(
    upcoming_only: bool = Query(True),
    current_doctor=Depends(get_current_doctor),
):
    query = {"doctor_id": _doctor_id(current_doctor)}

    if upcoming_only:
        query["scheduled_at"] = {"$gte": datetime.now()}
        query["status"] = {"$in": ["requested", "confirmed"]}

    rows = appointments_collection.find(query, {"_id": 0}).sort("scheduled_at", 1)

    return [to_out(AppointmentRepository._with_related_data(a)) for a in rows]


@router.get(
    "/doctor/patients",
    response_model=list[schemas.PatientSummaryResponse],
)
def doctor_patients(current_doctor=Depends(get_current_doctor)):
    doctor_id = _doctor_id(current_doctor)

    patient_ids = set(
        appointments_collection.distinct("patient_id", {"doctor_id": doctor_id})
    )
    patient_ids |= set(
        doctor_assignments_collection.distinct("patient_id", {"doctor_id": doctor_id})
    )

    patients = patients_collection.find(
        {"patient_id": {"$in": list(patient_ids)}, "is_active": True},
        {"_id": 0},
    ).sort("patient_id", 1)

    return [to_list_item(p) for p in patients]