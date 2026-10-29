from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import psycopg
from app.core.config import settings
import asyncio

from pydantic import BaseModel, Field

from app.rag.store import ingest_document
from pydantic import BaseModel
from app.agents.sql_agent import ask_sql_agent
from app.graph.workflow import workflow


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)


class DocumentIngestRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=100000)



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



@app.post("/chat/sql")
async def chat_sql(request: ChatRequest):
    answer = await ask_sql_agent(request.question)
    return {"answer": answer}

@app.post("/chat")
async def chat(request: ChatRequest):
    result = await workflow.ainvoke({
        "question": request.question,
        "errors": [],
    })

    return {
        "question": request.question,
        "intent": result.get("intent"),
        "answer": result.get(
            "final_answer",
            result.get("sql_result", "No answer generated."),
        ),
        "errors": result.get("errors", []),
    }


@app.post("/documents/ingest")
async def ingest_document_endpoint(request: DocumentIngestRequest):
    chunk_count = await asyncio.to_thread(
        ingest_document,
        request.title,
        request.text,
    )

    return {
        "status": "indexed",
        "title": request.title,
        "chunks_indexed": chunk_count,
    }
