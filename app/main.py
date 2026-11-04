import asyncio
import secrets
import uuid

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, SecretStr
from langgraph.types import Command

from app.core.config import settings
from app.graph.workflow import workflow
from app.observability.tracing import run_traced_workflow
from app.rag.store import ingest_document
from app.schemas.chat import ChatRequest
from app.security.input_guard import validate_user_input


class DocumentIngestRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=100000)


class ApprovalRequest(BaseModel):
    approval_token: SecretStr


_approval_locks: dict[str, asyncio.Lock] = {}


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
    return await _start_chat(request, force_sql=True)

@app.post("/chat")
async def chat(request: ChatRequest):
    return await _start_chat(request)


async def _start_chat(
    request: ChatRequest,
    force_sql: bool = False,
) -> dict:
    check = validate_user_input(request.question)

    if not check.allowed:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Request rejected by security validation",
                "reason": check.reason,
            },
        )

    request_id = str(uuid.uuid4())
    approval_token = secrets.token_urlsafe(32)
    initial_state = {
        "question": request.question,
        "request_id": request_id,
        "approval_token": approval_token,
    }
    if force_sql:
        initial_state["intent"] = "sql"

    config = {"configurable": {"thread_id": request_id}}
    result = await run_traced_workflow(
        workflow=workflow,
        question=request.question,
        config=config,
        state=initial_state,
    )

    if result.get("approval_status") == "pending":
        return {
            "status": "approval_required",
            "request_id": request_id,
            "approval_token": approval_token,
            "question": request.question,
            "sql": result.get("sql_query", ""),
            "message": "Review this SQL, then approve or reject it.",
        }

    return {
        "question": request.question,
        "intent": result.get("intent"),
        "status": "completed",
        "answer": result.get(
            "final_answer",
            result.get(
                "sql_result",
                result.get(
                    "document_result",
                    "No answer generated.",
                ),
            ),
        ),
        "errors": result.get("errors", []),
    }


async def _resolve_approval(
    request_id: str,
    request: ApprovalRequest,
    approved: bool,
) -> dict:
    lock = _approval_locks.setdefault(request_id, asyncio.Lock())
    async with lock:
        config = {"configurable": {"thread_id": request_id}}
        snapshot = await workflow.aget_state(config)
        state = snapshot.values or {}

        if not state:
            raise HTTPException(status_code=404, detail="Approval request not found")
        if state.get("approval_status") != "pending":
            raise HTTPException(
                status_code=409,
                detail="Approval request is no longer pending",
            )

        expected_token = state.get("approval_token", "")
        supplied_token = request.approval_token.get_secret_value()
        if not expected_token or not secrets.compare_digest(
            expected_token,
            supplied_token,
        ):
            raise HTTPException(status_code=403, detail="Invalid approval token")

        result = await workflow.ainvoke(
            Command(resume={"approved": approved}),
            config=config,
        )

    if approved:
        return {
            "status": "completed",
            "request_id": request_id,
            "answer": result.get("final_answer", "SQL query completed."),
            "errors": result.get("errors", []),
        }

    return {
        "status": "rejected",
        "request_id": request_id,
        "answer": result.get(
            "final_answer",
            "The SQL query was rejected and not executed.",
        ),
    }


@app.post("/approvals/{request_id}/approve")
async def approve_sql(request_id: str, request: ApprovalRequest):
    return await _resolve_approval(request_id, request, approved=True)


@app.post("/approvals/{request_id}/reject")
async def reject_sql(request_id: str, request: ApprovalRequest):
    return await _resolve_approval(request_id, request, approved=False)


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
