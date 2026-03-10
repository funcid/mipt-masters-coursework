import asyncio
import json
import os
from contextlib import asynccontextmanager, suppress

from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "lesson-messages")


class MessageIn(BaseModel):
    message: str


async def create_producer_with_retries(max_attempts: int = 30) -> AIOKafkaProducer:
    for attempt in range(1, max_attempts + 1):
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
        try:
            await producer.start()
            return producer
        except Exception:  # noqa: BLE001
            with suppress(Exception):
                await producer.stop()
            if attempt == max_attempts:
                raise
            await asyncio.sleep(2)
    raise RuntimeError("Could not connect to Kafka")


@asynccontextmanager
async def lifespan(app: FastAPI):
    producer = await create_producer_with_retries()
    app.state.producer = producer
    try:
        yield
    finally:
        await producer.stop()


app = FastAPI(title="lesson-producer", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/messages")
async def create_message(data: MessageIn) -> dict[str, str]:
    payload = data.model_dump()
    try:
        await app.state.producer.send_and_wait(KAFKA_TOPIC, payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Kafka unavailable: {exc}") from exc
    return {"status": "queued"}
