from fastapi import FastAPI

app = FastAPI(title="app1")


@app.get("/data")
def get_data() -> dict[str, str]:
    return {
        "service": "app1",
        "message": "Hello from internal service",
    }
