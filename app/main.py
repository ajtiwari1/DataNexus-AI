from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg
from app.core.config import settings

app = FastAPI(
    title="DataNexus AI",
    description="Enterprise Data Intelligence Multi-Agent Platform",
    version="0.1.0",
)

class HealthResponse(BaseModel):
    status: str
    service: str

@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="datanexus-api")

@app.get("/ready", tags=["health"])
def ready() -> dict[str, str]:
    try:
        with psycopg.connect(settings.database_url, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        return {"status": "ready", "database": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is not ready") from exc
