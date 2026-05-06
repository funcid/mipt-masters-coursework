import asyncio
import json
import os
from contextlib import asynccontextmanager, suppress

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "lesson-messages")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "lesson-consumer")


async def consume_forever(app: FastAPI) -> None:
    while True:
        consumer = AIOKafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=KAFKA_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        )
        try:
            await consumer.start()
            app.state.consumer = consumer
            async for msg in consumer:
                print(f"[topic={msg.topic} partition={msg.partition}] {msg.value}", flush=True)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            await asyncio.sleep(2)
        finally:
            with suppress(Exception):
                await consumer.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(consume_forever(app))
    app.state.consumer_task = task
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="lesson-consumer", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
