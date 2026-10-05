from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.mongodb import guardians_collection, doctors_collection


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/login"
)


credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


# =====================================================================
# PASSWORD
# =====================================================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt(),
    ).decode()


def verify_password(
    plain: str,
    hashed: str,
) -> bool:
    return bcrypt.checkpw(
        plain.encode(),
        hashed.encode(),
    )


# =====================================================================
# JWT
# =====================================================================

def verify_token(token: str) -> dict:
    """Decode and validate a JWT."""
    return _decode(token)


def create_access_token(
    subject_id: int,
    role: str,
    token_type: str = "guardian",
) -> str:

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(subject_id),
        "role": role,
        "type": token_type,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def _decode(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except JWTError:
        raise credentials_error


# =====================================================================
# CURRENT GUARDIAN
# =====================================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
):
    payload = _decode(token)

    # Doctor token cannot access guardian endpoints
    if payload.get("type") == "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires a guardian account",
        )

    guardian_id = payload.get("sub")

    if guardian_id is None:
        raise credentials_error

    try:
        guardian_id = int(guardian_id)
    except (TypeError, ValueError):
        raise credentials_error

    guardian = guardians_collection.find_one(
        {
            "guardian_id": guardian_id,
            "is_active": True,
        },
        {
            "_id": 0,
        },
    )

    if guardian is None:
        raise credentials_error

    return guardian


# =====================================================================
# CURRENT DOCTOR
# =====================================================================

def get_current_doctor(
    token: str = Depends(oauth2_scheme),
):
    payload = _decode(token)

    # Guardian token cannot access doctor endpoints
    if payload.get("type") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires a doctor account",
        )

    doctor_id = payload.get("sub")

    if doctor_id is None:
        raise credentials_error

    try:
        doctor_id = int(doctor_id)
    except (TypeError, ValueError):
        raise credentials_error

    doctor = doctors_collection.find_one(
        {
            "doctor_id": doctor_id,
            "is_active": True,
        },
        {
            "_id": 0,
        },
    )

    if doctor is None:
        raise credentials_error

    return doctor


# =====================================================================
# STAFF AUTHORIZATION
# =====================================================================

def require_staff(
    current_user=Depends(get_current_user),
):
    if current_user.get("role") != "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )

    return current_user