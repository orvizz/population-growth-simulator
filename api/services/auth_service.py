"""
AuthService — business logic for user registration and authentication.

Responsibilities:
- Enforce uniqueness constraints (username, email) with meaningful errors.
- Hash and verify passwords.
- Issue JWT tokens.

The service raises HTTPException directly so that FastAPI can handle them
consistently regardless of which controller calls the service.
"""
import bcrypt
from fastapi import HTTPException, status

from api.records import UserRecord
from api.repositories.user_repository import UserRepository
from api.schemas import Token, UserCreate
from api.deps import create_access_token


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def register(self, data: UserCreate) -> UserRecord:
        """Create a new user account. Raises 409 if username or email is taken.

        The `detail` is a stable error code (not display text) so the frontend
        can map it to a localized message via the i18n engine.
        """
        if self._repo.get_by_username(data.username):
            raise HTTPException(status_code=409, detail="username_taken")
        if self._repo.get_by_email(data.email):
            raise HTTPException(status_code=409, detail="email_taken")

        user = self._repo.create(
            username=data.username,
            email=data.email,
            password_hash=self._hash(data.password),
        )
        return UserRecord.model_validate(user)

    def authenticate(self, username: str, password: str) -> Token:
        """Verify credentials and return a Bearer token. Raises 401 on failure."""
        user = self._repo.get_by_username(username)
        if not user or not self._verify(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid_credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return Token(access_token=create_access_token(user.id))

    def get_by_id(self, user_id: int) -> UserRecord | None:
        user = self._repo.get_by_id(user_id)
        return UserRecord.model_validate(user) if user else None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hash(plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def _verify(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
