import pytest

from app.graph.nodes import sql_node, rag_node_wrapper


@pytest.mark.asyncio
async def test_sql_failure_does_not_affect_rag(monkeypatch):
    async def fail_sql(question):
        raise RuntimeError("SQL unavailable")

    async def successful_rag(state):
        return {
            "document_result": "Revenue declined due to lower sales.",
            "retrieved_context": ["Sales report"],
        }

    monkeypatch.setattr(
        "app.graph.nodes.ask_sql_agent",
        fail_sql,
    )
    monkeypatch.setattr(
        "app.graph.nodes.rag_node",
        successful_rag,
    )

    state = {
        "question": "Why did revenue decline?",
        "intent": "both",
        "errors": [],
    }

    sql_result, rag_result = await asyncio.gather(
        sql_node(state),
        rag_node_wrapper(state),
    )

    assert sql_result["sql_result"] == ""
    assert rag_result["document_result"]
    assert any("SQL agent failed" in e for e in sql_result["errors"])