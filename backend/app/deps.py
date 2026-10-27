from typing import Optional, TypeVar

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, get_db
from .enums import UserRole
from .models import AppUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

EDITOR_ROLES = (UserRole.admin, UserRole.tehsildar, UserRole.patwari)
MANAGER_ROLES = (UserRole.admin, UserRole.tehsildar)
ADMIN_ROLES = (UserRole.admin,)

ModelT = TypeVar("ModelT", bound=Base)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AppUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        raise credentials_error from None

    user = db.get(AppUser, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_roles(*roles: UserRole):
    def dependency(user: AppUser = Depends(get_current_user)) -> AppUser:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency


def get_or_404(
    db: Session,
    model: type[ModelT],
    record_id: Optional[int],
    name: str = "Resource",
) -> ModelT:
    obj = db.get(model, record_id) if record_id is not None else None
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return obj


def db_error(exc: DBAPIError) -> HTTPException:
    message = str(getattr(exc, "orig", exc))
    lower = message.lower()
    if "cannot exceed 100%" in message:
        return HTTPException(
            status_code=409,
            detail="Total ownership share for this khasra cannot exceed 100%",
        )
    if "duplicate entry" in lower:
        return HTTPException(status_code=409, detail="Duplicate record")
    if "foreign key constraint" in lower:
        return HTTPException(
            status_code=400, detail="Referenced record does not exist or is in use"
        )
    if "data too long" in lower:
        return HTTPException(status_code=422, detail="A value is too long")
    return HTTPException(status_code=409, detail="Database constraint violation")
