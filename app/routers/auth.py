from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import (
    create_access_token,
    verify_password,
    hash_password,
    get_current_user,
    get_current_doctor,
)
from app.database import get_db

router = APIRouter()


@router.post("/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    guardian = (
        db.query(models.Guardian)
        .filter(models.Guardian.mobile_number == payload.mobile_number)
        .first()
    )

    if not guardian or not verify_password(payload.password, guardian.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect mobile number or password",
        )

    if not guardian.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive",
        )

    token = create_access_token(guardian.guardian_id, guardian.role)
    return schemas.TokenResponse(access_token=token)


@router.get("/auth/me", response_model=schemas.GuardianMe)
def read_me(current_user: models.Guardian = Depends(get_current_user)):
    return current_user


@router.post("/auth/doctor-login", response_model=schemas.DoctorTokenResponse)
def doctor_login(payload: schemas.DoctorLoginRequest, db: Session = Depends(get_db)):
    doctor = (
        db.query(models.Doctor)
        .filter(models.Doctor.staff_id == payload.staff_id.strip().upper())
        .first()
    )

    if not doctor or not verify_password(payload.password, doctor.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect staff ID or password",
        )

    if not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive",
        )

    token = create_access_token(doctor.doctor_id, "doctor", token_type="doctor")

    return schemas.DoctorTokenResponse(
        access_token=token,
        must_change_password=doctor.must_change_password,
        doctor_name=f"{doctor.first_name} {doctor.last_name}",
    )


@router.get("/auth/doctor/me", response_model=schemas.DoctorMe)
def doctor_me(current_doctor: models.Doctor = Depends(get_current_doctor)):
    return current_doctor


@router.post("/auth/doctor/change-password")
def change_doctor_password(
    payload: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_doctor: models.Doctor = Depends(get_current_doctor),
):
    if not verify_password(payload.current_password, current_doctor.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_doctor.password_hash = hash_password(payload.new_password)
    current_doctor.must_change_password = False
    db.commit()

    return {"message": "Password updated"}