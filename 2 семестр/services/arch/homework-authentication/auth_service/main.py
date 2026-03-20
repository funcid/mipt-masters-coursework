import os
import re
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import FastAPI, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import Integer, String, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/auth_demo",
)
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

app = FastAPI(title="auth_service")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)


class Credentials(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    token: str


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


def is_password_secure(password: str) -> bool:
    if len(password) < 8:
        return False
    has_upper = re.search(r"[A-Z]", password) is not None
    has_lower = re.search(r"[a-z]", password) is not None
    has_digit = re.search(r"\d", password) is not None
    has_special = re.search(r"[^A-Za-z0-9]", password) is not None
    return has_upper and has_lower and has_digit and has_special


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(credentials: Credentials) -> Response:
    if not is_password_secure(credentials.password):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    password_hash = hash_password(credentials.password)
    user = User(email=credentials.email, password=password_hash)

    try:
        with Session(engine) as session:
            session.add(user)
            session.commit()
    except IntegrityError:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    return Response(status_code=status.HTTP_201_CREATED)


@app.post("/auth", response_model=TokenResponse)
def authenticate(credentials: Credentials) -> TokenResponse | Response:
    with Session(engine) as session:
        stmt = select(User).where(User.email == credentials.email)
        user = session.scalar(stmt)

    if user is None or not verify_password(credentials.password, user.password):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    exp = datetime.now(tz=timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    token = jwt.encode({"user_id": user.id, "exp": exp}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return TokenResponse(token=token)
