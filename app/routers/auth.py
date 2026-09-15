from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import create_access_token, verify_password, get_current_user
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