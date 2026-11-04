from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app import main
from app.main import ApprovalRequest


class FakeWorkflow:
    def __init__(self, state):
        self.state = state
        self.resume_calls = []

    async def aget_state(self, config):
        assert config["configurable"]["thread_id"] == "request-1"
        return SimpleNamespace(values=self.state)

    async def ainvoke(self, command, config):
        self.resume_calls.append((command, config))
        return {
            "approval_status": "approved",
            "final_answer": "SQL result",
            "errors": [],
        }


@pytest.mark.asyncio
async def test_approval_api_requires_matching_capability_token(monkeypatch):
    fake_workflow = FakeWorkflow({
        "approval_status": "pending",
        "approval_token": "expected-token",
    })
    monkeypatch.setattr(main, "workflow", fake_workflow)

    with pytest.raises(HTTPException) as error:
        await main.approve_sql(
            "request-1",
            ApprovalRequest(approval_token="wrong-token"),
        )

    assert error.value.status_code == 403
    assert fake_workflow.resume_calls == []


@pytest.mark.asyncio
async def test_approval_api_resumes_pending_request(monkeypatch):
    fake_workflow = FakeWorkflow({
        "approval_status": "pending",
        "approval_token": "expected-token",
    })
    monkeypatch.setattr(main, "workflow", fake_workflow)

    result = await main.approve_sql(
        "request-1",
        ApprovalRequest(approval_token="expected-token"),
    )

    assert result["status"] == "completed"
    assert result["answer"] == "SQL result"
    assert len(fake_workflow.resume_calls) == 1
