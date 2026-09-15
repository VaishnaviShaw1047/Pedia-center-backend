from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.database import get_db

router = APIRouter()


@router.get("/patients", response_model=schemas.PatientListResponse)
def list_patients(
    search: str | None = Query(None, description="Name, MRN or guardian mobile"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = (
        db.query(models.Patient)
        .options(joinedload(models.Patient.guardian))
        .filter(models.Patient.is_active == True)
    )

    if search:
        term = f"%{search.strip()}%"
        query = query.join(models.Guardian).filter(
            or_(
                models.Patient.first_name.ilike(term),
                models.Patient.last_name.ilike(term),
                models.Patient.mrn.ilike(term),
                models.Guardian.mobile_number.ilike(term),
            )
        )

    total = query.count()

    patients = (
        query.order_by(models.Patient.patient_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        schemas.PatientListItem(
            patient_id=p.patient_id,
            mrn=p.mrn,
            first_name=p.first_name,
            last_name=p.last_name,
            date_of_birth=p.date_of_birth,
            gender=p.gender,
            blood_group=p.blood_group,
            guardian_name=f"{p.guardian.first_name} {p.guardian.last_name}",
            guardian_mobile=p.guardian.mobile_number,
        )
        for p in patients
    ]

    return schemas.PatientListResponse(
        total=total, page=page, page_size=page_size, items=items
    )


@router.get("/patients/{mrn}", response_model=schemas.PatientDetail)
def get_patient(mrn: str, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.mrn == mrn).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return patient


@router.patch("/patients/{mrn}", response_model=schemas.PatientDetail)
def update_patient(
    mrn: str,
    payload: schemas.PatientUpdate,
    db: Session = Depends(get_db),
):
    patient = db.query(models.Patient).filter(models.Patient.mrn == mrn).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    for field, value in changes.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)

    return patient