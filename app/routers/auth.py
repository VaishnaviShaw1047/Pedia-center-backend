"""Auth routes. HTTP only."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_doctor, get_current_user
from app.database import get_db
from app.service import AuthService

router = APIRouter()


# ---------- guardian ----------

@router.post("/auth/login", response_model=schemas.AuthTokenResponse)
def login(payload: schemas.GuardianLoginRequest, db: Session = Depends(get_db)):
    token = AuthService.login_guardian(db, payload.mobile_number, payload.password)
    return schemas.AuthTokenResponse(access_token=token)


@router.get("/auth/me", response_model=schemas.GuardianProfileResponse)
def read_me(current_user: models.Guardian = Depends(get_current_user)):
    return current_user


# ---------- doctor ----------

@router.post("/auth/doctor-login", response_model=schemas.DoctorTokenResponse)
def doctor_login(payload: schemas.DoctorLoginRequest, db: Session = Depends(get_db)):
    doctor = AuthService.login_doctor(db, payload.staff_id, payload.password)

    return schemas.DoctorTokenResponse(
        access_token=AuthService.doctor_token(doctor),
        must_change_password=doctor.must_change_password,
        doctor_name=f"{doctor.first_name} {doctor.last_name}",
    )


@router.get("/auth/doctor/me", response_model=schemas.DoctorProfileResponse)
def doctor_me(current_doctor: models.Doctor = Depends(get_current_doctor)):
    return current_doctor


@router.post("/auth/doctor/change-password")
def change_doctor_password(
    payload: schemas.PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_doctor: models.Doctor = Depends(get_current_doctor),
):
    AuthService.change_doctor_password(
        db, current_doctor, payload.current_password, payload.new_password
    )
    return {"message": "Password updated"}

