import asyncio
import pytest

from app.graph.state import DataNexusState


@pytest.mark.asyncio
async def test_parallel_agent_state_aggregation():
    state: DataNexusState = {
        "question": "Compare revenue with business reports",
        "intent": "both",
        "errors": [],
    }

    async def mock_sql_agent():
        await asyncio.sleep(0.1)
        return {
            "sql_result": "Revenue declined by 15%",
            "errors": ["SQL warning"],
        }

    async def mock_rag_agent():
        await asyncio.sleep(0.1)
        return {
            "document_result": "Lower sales caused the decline",
            "retrieved_context": ["Q3 report"],
            "errors": ["RAG warning"],
        }

    sql_update, rag_update = await asyncio.gather(
        mock_sql_agent(),
        mock_rag_agent(),
    )

    state["sql_result"] = sql_update["sql_result"]
    state["document_result"] = rag_update["document_result"]
    state["retrieved_context"] = rag_update["retrieved_context"]
    state["errors"] = (
        state["errors"]
        + sql_update["errors"]
        + rag_update["errors"]
    )

    assert state["sql_result"]
    assert state["document_result"]
    assert state["retrieved_context"] == ["Q3 report"]
    assert len(state["errors"]) == 2