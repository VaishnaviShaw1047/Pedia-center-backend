from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# AUTHENTICATION AND AUTHORIZATION LOGIC --------------------
# This is the security/logic layer.

# It handles things like:

# Hashing passwords
# Checking passwords
# Creating JWT tokens
# Decoding/verifying JWT tokens
# Finding the currently logged-in user
# Checking whether the user is an Admin
# Checking whether the user is a Doctor
# Protecting endpoints
# --------------------------------------------------

from app.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.mongodb import (
    guardians_collection,
    doctors_collection,
    users_collection,
)


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

    token_type = payload.get("type")
    user_id = payload.get("sub")

    if user_id is None:
        raise credentials_error

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise credentials_error

    # Admin token
    if token_type == "admin":
        user = users_collection.find_one(
            {
                "user_id": user_id,
                "is_active": True,
            },
            {"_id": 0},
        )

        if user is None:
            raise credentials_error

        return user

    # Doctor token cannot access these endpoints
    if token_type == "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires a guardian account",
        )

    # Guardian token
    guardian = guardians_collection.find_one(
        {
            "guardian_id": user_id,
            "is_active": True,
        },
        {"_id": 0},
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

#ADMIN-----------------------------------------------------------------------
def require_admin(
    current_user=Depends(get_current_user),
):
    role = current_user.get(
        "role",
        current_user.get("user_type"),
    )

    if role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user

#ADMIN-----------------------------------------------------------------------
def require_admin(
    current_user=Depends(get_current_user),
):
    role = current_user.get(
        "role",
        current_user.get("user_type"),
    )

    if role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user
