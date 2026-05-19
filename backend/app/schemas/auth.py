"""Pydantic schemas for auth endpoints."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


class UserRead(BaseModel):
    id: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
