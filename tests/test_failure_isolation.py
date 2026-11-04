import pytest

from app.graph.nodes import sql_generation_node


@pytest.mark.asyncio
async def test_sql_generation_failure_is_reported(monkeypatch):
    async def fail_generation(question):
        assert question == "Why did revenue decline?"
        raise RuntimeError("SQL unavailable")

    monkeypatch.setattr(
        "app.graph.nodes.generate_sql_query",
        fail_generation,
    )

    result = await sql_generation_node({
        "question": "Why did revenue decline?",
        "intent": "both",
        "errors": [],
    })

    assert result["sql_query"] == ""
    assert any(
        "SQL query generation failed" in error
        for error in result["errors"]
    )
