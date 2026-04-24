import re
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _validate_email(v: str) -> str:
    v = v.lower().strip()
    if not _EMAIL_RE.match(v):
        raise ValueError("Invalid email address.")
    return v


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return _validate_email(v)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return _validate_email(v)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
