"""User routes. HTTP only."""

from fastapi import APIRouter, Depends , Query

from app import schemas
from app.service import UserService
from app.auth import require_admin


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=schemas.UserListResponse)
def list_users(
    search: str | None = Query(None, description="Name or username"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    total, users = UserService.list_users(
        search,
        page,
        page_size,
    )

    return schemas.UserListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[
            schemas.UserDetailResponse(
                user_id=user["user_id"],
                first_name=user.get("first_name"),
                last_name=user.get("last_name"),
                username=user["username"],
                user_type=user["user_type"],
            )
            for user in users
        ],
    )


@router.get("/{user_id}", response_model=schemas.UserDetailResponse)
def get_user(user_id: int):
    user = UserService.get_user_by_id(user_id)

    return schemas.UserDetailResponse(
        user_id=user["user_id"],
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        username=user["username"],
        user_type=user["user_type"],
    )


@router.post("/{user_id}", response_model=schemas.UserDetailResponse)
def update_user(
    user_id: int,
    payload: schemas.UserUpdateRequest,
     _admin=Depends(require_admin),
):
    user = UserService.update_user(
        user_id,
        payload,
    )

    return schemas.UserDetailResponse(
        user_id=user["user_id"],
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        username=user["username"],
        user_type=user["user_type"],
    )


@router.delete("/{user_id}")
def delete_user(user_id: int, _admin=Depends(require_admin)):
    UserService.delete_user(user_id)

    return {"message": "User deleted successfully"}


@router.post("", response_model=schemas.UserDetailResponse)
def create_user(
    payload: schemas.UserCreateRequest,
    _admin=Depends(require_admin),
):
    user = UserService.create_user(payload)

    return schemas.UserDetailResponse(
        user_id=user["user_id"],
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        username=user["username"],
        user_type=user["user_type"],
    )


@router.post("/{user_id}/change-password")
def change_user_password(
    user_id: int,
    payload: schemas.PasswordChangeRequest,
):
    UserService.change_user_password(
        user_id,
        payload.current_password,
        payload.new_password,
    )

    return {"message": "Password updated successfully"}


@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    payload: schemas.PasswordChangeRequest,
):
    UserService.reset_user_password(
        user_id,
        payload.new_password,
    )

    return {"message": "Password reset successfully"}
