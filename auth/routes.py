"""Auth routes: register, login, me, update phone."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from auth.security import (
    create_token,
    get_current_user,
    hash_password,
    verify_password,
)
from db.repository import UserRepo


router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = ""
    phone: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PhoneIn(BaseModel):
    phone: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn):
    if UserRepo.find_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = UserRepo.create(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        phone=payload.phone,
    )
    token = create_token(user["id"], user["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _public_user(user),
    }


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn):
    user = UserRepo.find_by_email(payload.email)
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    user["id"] = str(user["_id"])
    token = create_token(user["id"], user["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _public_user(user),
    }


# Optional: also accept OAuth2 form (so docs Authorize button works)
@router.post("/token", response_model=TokenOut)
def login_form(form: OAuth2PasswordRequestForm = Depends()):
    return login(LoginIn(email=form.username, password=form.password))


@router.get("/me")
def me(current=Depends(get_current_user)):
    user = UserRepo.find_by_id(current["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _public_user(user)


@router.put("/me/phone")
def update_phone(payload: PhoneIn, current=Depends(get_current_user)):
    UserRepo.update_phone(current["id"], payload.phone.strip())
    user = UserRepo.find_by_id(current["id"])
    return _public_user(user)


# ---------------------------------------------------------------------------
def _public_user(user: dict) -> dict:
    return {
        "id": user.get("id") or str(user.get("_id")),
        "email": user.get("email"),
        "name": user.get("name", ""),
        "phone": user.get("phone", ""),
    }

