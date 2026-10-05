"""Auth routes. HTTP only."""

from fastapi import APIRouter, Depends

from app import schemas
from app.auth import get_current_doctor, get_current_user
from app.service import AuthService

router = APIRouter()


# =====================================================================
# GUARDIAN
# =====================================================================

@router.post(
    "/auth/login",
    response_model=schemas.AuthTokenResponse,
)
def login(
    payload: schemas.GuardianLoginRequest,
):
    token = AuthService.login_guardian(
        payload.mobile_number,
        payload.password,
    )

    return schemas.AuthTokenResponse(
        access_token=token,
    )


@router.get(
    "/auth/me",
    response_model=schemas.GuardianProfileResponse,
)
def read_me(
    current_user=Depends(get_current_user),
):
    return current_user


# =====================================================================
# DOCTOR
# =====================================================================

@router.post(
    "/auth/doctor-login",
    response_model=schemas.DoctorTokenResponse,
)
def doctor_login(
    payload: schemas.DoctorLoginRequest,
):
    doctor = AuthService.login_doctor(
        payload.staff_id,
        payload.password,
    )

    return schemas.DoctorTokenResponse(
        access_token=AuthService.doctor_token(doctor),
        must_change_password=doctor.get(
            "must_change_password",
            False,
        ),
        doctor_name=(
            f"{doctor['first_name']} "
            f"{doctor['last_name']}"
        ),
    )


@router.get(
    "/auth/doctor/me",
    response_model=schemas.DoctorProfileResponse,
)
def doctor_me(
    current_doctor=Depends(get_current_doctor),
):
    return current_doctor


# =====================================================================
# DOCTOR PASSWORD
# =====================================================================

@router.post(
    "/auth/doctor/change-password",
)
def change_doctor_password(
    payload: schemas.PasswordChangeRequest,
    current_doctor=Depends(get_current_doctor),
):
    AuthService.change_doctor_password(
        current_doctor,
        payload.current_password,
        payload.new_password,
    )

    return {
        "message": "Password updated"
    }