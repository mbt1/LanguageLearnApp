# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ── Registration ──────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None


class RegisterResponse(BaseModel):
    user_id: UUID
    email: str
    access_token: str
    message: str


# ── Login ─────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user_id: UUID
    email: str
    email_verified: bool
    access_token: str


# ── Token refresh ─────────────────────────────────────
class RefreshResponse(BaseModel):
    access_token: str


# ── Email verification ────────────────────────────────
class VerifyEmailResponse(BaseModel):
    message: str


# ── User context (from JWT) ───────────────────────────
class CurrentUser(BaseModel):
    user_id: UUID
    email: str
    email_verified: bool


# ── Passkey schemas ───────────────────────────────────
class PasskeyRegistrationOptionsResponse(BaseModel):
    options: str  # JSON string from options_to_json()


class PasskeyRegistrationVerifyRequest(BaseModel):
    credential: str  # JSON string from navigator.credentials.create()
    name: str | None = None


class PasskeyRegistrationVerifyResponse(BaseModel):
    message: str


class PasskeyAuthenticationOptionsRequest(BaseModel):
    email: EmailStr


class PasskeyAuthenticationOptionsResponse(BaseModel):
    options: str  # JSON string from options_to_json()


class PasskeyAuthenticationVerifyRequest(BaseModel):
    email: EmailStr
    credential: str  # JSON string from navigator.credentials.get()


class PasskeyAuthenticationVerifyResponse(BaseModel):
    user_id: UUID
    email: str
    email_verified: bool
    access_token: str


class PasskeyListItem(BaseModel):
    id: UUID
    name: str | None
    created_at: str
