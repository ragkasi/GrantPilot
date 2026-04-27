"""User creation and lookup."""
import uuid

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User


def _user_id() -> str:
    return f"user_{uuid.uuid4().hex[:12]}"


def create_user(db: Session, email: str, password: str, is_demo: bool = False) -> User:
    user = User(
        id=_user_id(),
        email=email.lower().strip(),
        hashed_password=hash_password(password),
        is_demo=is_demo,
    )
    db.add(user)
    db.flush()
    return user


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower().strip()).first()


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str) -> bool:
    """Verify current password, then set the new one. Returns False if current is wrong."""
    if not verify_password(current_password, user.hashed_password):
        return False
    user.hashed_password = hash_password(new_password)
    db.flush()
    return True
