"""Patient routes. HTTP only."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.service import PatientService, UserService


router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=schemas.UserListResponse)
def list_users(
    search: str | None = Query(None, description="Name or username"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total, users = UserService.list_users(db, search, page, page_size)

    return schemas.UserListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[schemas.UserDetails(
            user_id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            role=user.role
        ) for user in users],
    )
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = UserService.get_user_by_id(db, user_id)
    return schemas.UserDetailResponse(
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
       role=user.role,
    )
@router.post("/{user_id}", response_model=schemas.UserListResponse)
def update_user(
    user_id: int,
    payload: schemas.UserUpdateRequest,
    db: Session = Depends(get_db),
):
    return UserService.update_user(db, user_id, payload) 

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    UserService.delete_user(db, user_id)
    return {"message": "User deleted successfully"}  

@router.post("", response_model=schemas.UserListResponse)
def create_user(
    payload: schemas.UserCreateRequest,
    db: Session = Depends(get_db),
):
    user_data= models.User(
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        user_type=payload.user_type
    )
    user = UserService.create_user(db, user_data)
    return schemas.UserDetailResponse(
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        user_type=user.user_type,
    )
@router.post("/{user_id}/change-password}", response_model=schemas.UserListResponse)
def change_user_password(
    user_id: int,
    payload: schemas.PasswordChangeRequest,
    db: Session = Depends(get_db),
):
    UserService.change_user_password(db, user_id, payload.current_password, payload.new_password)
    return {"message": "Password updated successfully"}  
   
@router.post("/{user_id}/reset-password}", response_model=schemas.UserListResponse)
def reset_user_password(
    user_id: int,
    payload: schemas.PasswordChangeRequest,
    db: Session = Depends(get_db),
):
    UserService.reset_user_password(db, user_id, payload.new_password)
    return {"message": "Password reset successfully"}


@router.get("/{user_id}", response_model=schemas.UserListResponse)
def get_user_by_user_id(user_id: int, db: Session = Depends(get_db)):
    user = UserService.get_user_by_id(db, user_id)
    return schemas.UserDetailResponse(
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        role=user.role,
    )

