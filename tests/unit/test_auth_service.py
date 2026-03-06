"""
Unit tests for AuthService (api/services/auth_service.py).

The repository is replaced with a MagicMock so no database is needed.
"""
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from api.schemas import UserCreate
from api.services.auth_service import AuthService


# Ensure JWT_SECRET_KEY is set for token creation
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")


def _make_user(**kwargs):
    """Build a minimal fake User ORM object."""
    import bcrypt
    defaults = {
        "id": 1,
        "username": "alice",
        "email": "alice@example.com",
        "password_hash": bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
        "created_at": datetime(2024, 1, 1),
    }
    defaults.update(kwargs)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_creates_user_and_returns_record(self):
        repo = MagicMock()
        repo.get_by_username.return_value = None
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()

        svc = AuthService(repo)
        result = svc.register(UserCreate(
            username="alice", email="alice@example.com", password="password123"
        ))

        repo.create.assert_called_once()
        assert result.username == "alice"

    def test_hashes_password_before_storing(self):
        import bcrypt
        repo = MagicMock()
        repo.get_by_username.return_value = None
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()

        svc = AuthService(repo)
        svc.register(UserCreate(
            username="alice", email="alice@example.com", password="password123"
        ))

        stored_hash = repo.create.call_args.kwargs["password_hash"]
        assert bcrypt.checkpw(b"password123", stored_hash.encode())

    def test_raises_409_on_duplicate_username(self):
        repo = MagicMock()
        repo.get_by_username.return_value = _make_user()

        svc = AuthService(repo)
        with pytest.raises(HTTPException) as exc:
            svc.register(UserCreate(
                username="alice", email="other@example.com", password="password123"
            ))
        assert exc.value.status_code == 409
        assert "username" in exc.value.detail.lower()

    def test_raises_409_on_duplicate_email(self):
        repo = MagicMock()
        repo.get_by_username.return_value = None
        repo.get_by_email.return_value = _make_user()

        svc = AuthService(repo)
        with pytest.raises(HTTPException) as exc:
            svc.register(UserCreate(
                username="other", email="alice@example.com", password="password123"
            ))
        assert exc.value.status_code == 409
        assert "email" in exc.value.detail.lower()

    def test_does_not_call_create_on_duplicate(self):
        repo = MagicMock()
        repo.get_by_username.return_value = _make_user()

        svc = AuthService(repo)
        with pytest.raises(HTTPException):
            svc.register(UserCreate(
                username="alice", email="a@b.com", password="password123"
            ))
        repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# authenticate
# ---------------------------------------------------------------------------

class TestAuthenticate:
    def test_returns_token_for_valid_credentials(self):
        user = _make_user()
        repo = MagicMock()
        repo.get_by_username.return_value = user

        svc = AuthService(repo)
        token = svc.authenticate("alice", "password123")

        assert token.access_token
        assert token.token_type == "bearer"

    def test_raises_401_for_wrong_password(self):
        user = _make_user()
        repo = MagicMock()
        repo.get_by_username.return_value = user

        svc = AuthService(repo)
        with pytest.raises(HTTPException) as exc:
            svc.authenticate("alice", "wrongpassword")
        assert exc.value.status_code == 401

    def test_raises_401_for_unknown_user(self):
        repo = MagicMock()
        repo.get_by_username.return_value = None

        svc = AuthService(repo)
        with pytest.raises(HTTPException) as exc:
            svc.authenticate("nobody", "password123")
        assert exc.value.status_code == 401


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

class TestGetById:
    def test_returns_user_record(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _make_user(id=5)

        svc = AuthService(repo)
        result = svc.get_by_id(5)
        assert result.id == 5

    def test_returns_none_when_not_found(self):
        repo = MagicMock()
        repo.get_by_id.return_value = None

        svc = AuthService(repo)
        assert svc.get_by_id(999) is None
