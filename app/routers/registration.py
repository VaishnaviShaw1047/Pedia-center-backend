import uuid

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth import hash_password

from app import models, schemas
from app.database import get_db
from app.auth import hash_password

router = APIRouter()





def generate_mrn(patient_id: int) -> str:
    return f"PC-2026-{patient_id:06d}"


@router.post(
    "/registration",
    response_model=schemas.RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_guardian(payload: schemas.GuardianCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(models.Guardian)
        .filter(models.Guardian.mobile_number == payload.mobile_number)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This mobile number is already registered",
        )

    guardian = models.Guardian(
        first_name=payload.first_name,
        last_name=payload.last_name,
        relationship_to_child=payload.relationship_to_child,
        mobile_number=payload.mobile_number,
        email=payload.email,
        password_hash=hash_password(payload.password),
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        city=payload.city,
        state=payload.state,
        pincode=payload.pincode,
        preferred_language=payload.preferred_language,
        terms_accepted=payload.terms_accepted,
        health_data_consent=payload.health_data_consent,
    )

    db.add(guardian)
    db.flush()

    created = []
    for child in payload.children:
        patient = models.Patient(
            patient_uid=str(uuid.uuid4()),
            mrn="",
            guardian_id=guardian.guardian_id,
            first_name=child.first_name,
            last_name=child.last_name,
            date_of_birth=child.date_of_birth,
            gender=child.gender,
            abha_id=child.abha_id,
            aadhaar_number=child.aadhaar_number,
            blood_group=child.blood_group,
            known_allergies=child.known_allergies,
            existing_conditions=child.existing_conditions,
            current_medications=child.current_medications,
            immunization_status=child.immunization_status,
            referred_by=child.referred_by,
        )
        db.add(patient)
        db.flush()

        patient.mrn = generate_mrn(patient.patient_id)
        created.append(patient)

    db.commit()

    return schemas.RegistrationResponse(
        guardian_id=guardian.guardian_id,
        patients=[schemas.PatientOut.model_validate(p) for p in created],
        message="Registration successful",
    )