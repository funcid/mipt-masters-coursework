import asyncio
import json
import os
from contextlib import asynccontextmanager, suppress

import asyncpg
from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "errors")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "errors-writer")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "errors_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "errors_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "errors_pass")


async def connect_postgres_with_retries(max_attempts: int = 30) -> asyncpg.Pool:
    dsn = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    for attempt in range(1, max_attempts + 1):
        try:
            return await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)
        except Exception:  # noqa: BLE001
            if attempt == max_attempts:
                raise
            await asyncio.sleep(2)
    raise RuntimeError("Could not connect to PostgreSQL")


async def ensure_table(pool: asyncpg.Pool) -> None:
    query = """
    CREATE TABLE IF NOT EXISTS errors (
        id BIGSERIAL PRIMARY KEY,
        time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        code INTEGER NOT NULL,
        message TEXT NOT NULL,
        details TEXT NOT NULL
    );
    """
    async with pool.acquire() as conn:
        await conn.execute(query)


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
                payload = msg.value
                async with app.state.db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO errors (code, message, details)
                        VALUES ($1, $2, $3);
                        """,
                        payload["code"],
                        payload["message"],
                        payload["details"],
                    )
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            await asyncio.sleep(2)
        finally:
            with suppress(Exception):
                await consumer.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await connect_postgres_with_retries()
    app.state.db_pool = pool
    await ensure_table(pool)
    task = asyncio.create_task(consume_forever(app))
    app.state.consumer_task = task
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        await pool.close()


app = FastAPI(title="error-consumer", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
