import os
from datetime import datetime, timezone

import jwt
from fastapi import FastAPI, Header, Response, status
from jwt import ExpiredSignatureError, InvalidSignatureError, PyJWTError
from pydantic import BaseModel
from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/auth_demo",
)
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

app = FastAPI(title="post_service")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)


class MessageIn(BaseModel):
    message: str


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


def extract_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", maxsplit=1)
    if len(parts) != 2 or parts[0] != "Bearer":
        return None
    return parts[1]


@app.post("/messages", status_code=status.HTTP_201_CREATED)
def create_message(
    payload: MessageIn,
    authorization: str | None = Header(default=None),
) -> Response:
    token = extract_token(authorization)
    if not token:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    except InvalidSignatureError:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    except PyJWTError:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    user_id = decoded.get("user_id")
    if not isinstance(user_id, int):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    with Session(engine) as session:
        session.add(
            Message(
                user_id=user_id,
                time=datetime.now(tz=timezone.utc),
                message=payload.message,
            )
        )
        session.commit()

    return Response(status_code=status.HTTP_201_CREATED)
