import os

import httpx
from fastapi import FastAPI, HTTPException

APP1_HOST = os.getenv("APP1_HOST", "app1")
APP1_PORT = os.getenv("APP1_PORT", "8000")
APP1_URL = f"http://{APP1_HOST}:{APP1_PORT}/data"

app = FastAPI(title="app2")


@app.get("/")
async def get_external_response() -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(APP1_URL)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to reach app1: {exc}") from exc

    return {
        "service": "app2",
        "source_url": APP1_URL,
        "app1_response": response.json(),
    }
