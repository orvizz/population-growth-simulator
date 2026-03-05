"""
UserRepository — pure data access for the users table.

No business logic, no HTTP concerns. Returns ORM objects only.
"""
from sqlalchemy.orm import Session

from db.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self._db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self._db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> User | None:
        return self._db.query(User).filter(User.email == email).first()

    def create(self, username: str, email: str, password_hash: str) -> User:
        user = User(username=username, email=email, password_hash=password_hash)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
