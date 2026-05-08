import os
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin123!")

app = FastAPI(title="Auth Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8100"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

users: dict[str, dict[str, str | int]] = {
    DEFAULT_ADMIN_EMAIL: {"password": DEFAULT_ADMIN_PASSWORD, "user_id": 1}
}


class Credentials(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    token: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: Credentials) -> dict[str, str]:
    key = str(payload.email).lower()
    if key in users:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже существует")
    user_id = len(users) + 1
    users[key] = {"password": payload.password, "user_id": user_id}
    return {"status": "created"}


@app.post("/auth", response_model=TokenResponse)
def auth(payload: Credentials) -> TokenResponse:
    key = str(payload.email).lower()
    user = users.get(key)
    if user is None or user["password"] != payload.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")

    exp = datetime.now(UTC) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    token = jwt.encode({"user_id": int(user["user_id"]), "exp": exp}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return TokenResponse(token=token)
