"""
Auth controller — HTTP concerns only.

Parses requests, delegates to AuthService, returns records.
No business logic, no DB access.
"""
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from api.records import UserRecord
from api.schemas import Token, UserCreate
from api.deps import get_auth_service
from api.services.auth_service import AuthService

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserRecord, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, service: AuthService = Depends(get_auth_service)):
    return service.register(body)


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    """Accepts username + password as OAuth2 form data."""
    return service.authenticate(form.username, form.password)
