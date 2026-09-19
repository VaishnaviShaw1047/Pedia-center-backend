from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import models
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import get_db


#My API uses a Bearer token for authentication, and the login endpoint is located at /api/v1/auth/login
# Create the OAuth2 security dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


# Create a reusable credentials error , instead of raising same HTTPException multiple times, we can create a reusable credentials error and raise it whenever needed .
credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

# this function takes a pswrd and ret a hashed version of it using brcypt . hashed paswrd is stored in db instead of plain text for inhanced security . verify paswrd func checks if a plain text paswrd match the hashed paswrd stored in db .
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# this is used during login, You don't decrypt the hash.
# Instead, bcrypt checks whether the supplied password corresponds to the stored hash.
def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

# This function creates a JWT.
def create_access_token(subject_id: int, role: str, token_type: str = "guardian") -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(subject_id),
        "role": role,
        "type": token_type,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


#Calculate token expiration.
def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise credentials_error


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Guardian:
    payload = _decode(token)

    if payload.get("type") == "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires a guardian account",
        )

    guardian_id = payload.get("sub")
    if guardian_id is None:
        raise credentials_error

    guardian = (
        db.query(models.Guardian)
        .filter(models.Guardian.guardian_id == int(guardian_id))
        .first()
    )

    if guardian is None or not guardian.is_active:
        raise credentials_error

    return guardian


def get_current_doctor(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Doctor:
    # This function takes a JWT and attempts to decode/verify it.This checks things such as whether the token's signature is valid and whether its claims, including expiration, are acceptable to the JWT library.
    payload = _decode(token)
# Check account type
    if payload.get("type") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            # 403 → authentication is known, but the authenticated identity isn't permitted for this endpoint.
            detail="This endpoint requires a doctor account",
        )

    doctor_id = payload.get("sub")
    if doctor_id is None:
        raise credentials_error

    doctor = (
        db.query(models.Doctor)
        .filter(models.Doctor.doctor_id == int(doctor_id))
        .first()
    )

    if doctor is None or not doctor.is_active:
        raise credentials_error

    return doctor


def require_staff(current_user: models.Guardian = Depends(get_current_user)) -> models.Guardian:
    if current_user.role != "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )
    return current_user