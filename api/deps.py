"""
FastAPI dependency providers.

get_db              — yields a SQLAlchemy session
get_auth_service    — constructs AuthService with a UserRepository
get_matrix_service  — constructs MatrixService with a MatrixRepository
get_current_user    — decodes JWT, returns UserRecord (raises 401 on failure)

Keeping JWT logic here (rather than in the service) means it stays
separate from business logic and is easy to swap for a different auth
scheme without touching any service.
"""
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from db.session import SessionLocal

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)


# ---------------------------------------------------------------------------
# DB session
# ---------------------------------------------------------------------------

def get_db():
    with SessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# JWT helpers (used by AuthService and get_current_user)
# ---------------------------------------------------------------------------

def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> int:
    """Decode JWT and return user_id. Raises 401 on any failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# Service factories — inject via Depends()
# ---------------------------------------------------------------------------

def get_auth_service(db: Session = Depends(get_db)):
    from api.repositories.user_repository import UserRepository
    from api.services.auth_service import AuthService
    return AuthService(UserRepository(db))


def get_matrix_service(db: Session = Depends(get_db)):
    from api.repositories.matrix_repository import MatrixRepository
    from api.repositories.user_repository import UserRepository
    from api.services.matrix_service import MatrixService
    return MatrixService(MatrixRepository(db), UserRepository(db))


def get_simulation_service(db: Session = Depends(get_db)):
    from api.repositories.matrix_repository import MatrixRepository
    from api.repositories.simulation_repository import SimulationRepository
    from api.services.simulation_service import SimulationService
    return SimulationService(MatrixRepository(db), SimulationRepository(db))


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
):
    """Like get_current_user but returns None instead of raising 401."""
    if not token:
        return None
    try:
        from api.repositories.user_repository import UserRepository
        from api.services.auth_service import AuthService
        user_id = _decode_token(token)
        return AuthService(UserRepository(db)).get_by_id(user_id)
    except HTTPException:
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Resolve the JWT to a UserRecord. Raises 401 if invalid or user not found."""
    from api.repositories.user_repository import UserRepository
    from api.services.auth_service import AuthService

    user_id = _decode_token(token)
    user = AuthService(UserRepository(db)).get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
