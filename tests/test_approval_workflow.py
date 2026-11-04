import pytest
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

import app.graph.nodes as nodes
import app.graph.workflow as workflow_module


@pytest.mark.asyncio
@pytest.mark.parametrize("approved", [True, False])
async def test_sql_requires_approval_before_execution(monkeypatch, approved):
    executed_queries = []

    async def fixed_supervisor(_state):
        return {"intent": "sql"}

    async def generate_query(_question):
        return "SELECT id FROM customers"

    async def execute_query(query):
        executed_queries.append(query)
        return '[{"id": 1}]'

    monkeypatch.setattr(workflow_module, "supervisor_node", fixed_supervisor)
    monkeypatch.setattr(nodes, "generate_sql_query", generate_query)
    monkeypatch.setattr(nodes, "execute_sql_query", execute_query)

    app = workflow_module.build_workflow(checkpointer=MemorySaver())
    request_id = "approval-test"
    config = {"configurable": {"thread_id": request_id}}
    initial = await app.ainvoke(
        {
            "question": "List customers",
            "request_id": request_id,
            "approval_token": "test-token",
        },
        config=config,
    )

    assert initial["approval_status"] == "pending"
    assert initial["sql_query"] == "SELECT id FROM customers"
    assert executed_queries == []

    completed = await app.ainvoke(
        Command(resume={"approved": approved}),
        config=config,
    )

    if approved:
        assert completed["approval_status"] == "approved"
        assert executed_queries == ["SELECT id FROM customers"]
        assert completed["final_answer"] == '[{"id": 1}]'
    else:
        assert completed["approval_status"] == "rejected"
        assert executed_queries == []
        assert "rejected" in completed["final_answer"].lower()


@pytest.mark.asyncio
async def test_invalid_sql_is_not_presented_for_approval(monkeypatch):
    executed_queries = []

    async def fixed_supervisor(_state):
        return {"intent": "sql"}

    async def generate_query(_question):
        return "DELETE FROM customers"

    async def execute_query(query):
        executed_queries.append(query)
        return "unexpected"

    monkeypatch.setattr(workflow_module, "supervisor_node", fixed_supervisor)
    monkeypatch.setattr(nodes, "generate_sql_query", generate_query)
    monkeypatch.setattr(nodes, "execute_sql_query", execute_query)

    app = workflow_module.build_workflow(checkpointer=MemorySaver())
    result = await app.ainvoke(
        {
            "question": "Delete customers",
            "request_id": "invalid-sql",
            "approval_token": "test-token",
        },
        config={"configurable": {"thread_id": "invalid-sql"}},
    )

    assert result["approval_status"] == "invalid"
    assert result["pending_approval"] is False
    assert executed_queries == []
