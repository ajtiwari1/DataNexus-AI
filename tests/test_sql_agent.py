import json
from types import SimpleNamespace

import pytest

from app.agents import sql_agent


class FakeTool:
    def __init__(self, name, result=None):
        self.name = name
        self.result = result
        self.calls = []

    async def ainvoke(self, arguments):
        self.calls.append(arguments)
        return self.result


@pytest.mark.asyncio
async def test_sql_generator_does_not_receive_execution_tool(monkeypatch):
    tools = [
        FakeTool("list_tables"),
        FakeTool("describe_table"),
        FakeTool("run_readonly_query"),
    ]
    captured = {}

    class FakeMCPClient:
        def __init__(self, _servers):
            assert _servers

        async def get_tools(self):
            return tools

    def fake_create_react_agent(**agent_kwargs):
        captured.update(agent_kwargs)
        return object()

    monkeypatch.setattr(sql_agent, "MultiServerMCPClient", FakeMCPClient)
    monkeypatch.setattr(
        sql_agent,
        "ChatOpenAI",
        lambda **kwargs: kwargs,
    )
    monkeypatch.setattr(
        sql_agent,
        "create_react_agent",
        fake_create_react_agent,
    )

    await sql_agent.build_sql_agent()

    assert {tool.name for tool in captured["tools"]} == {
        "list_tables",
        "describe_table",
    }


@pytest.mark.asyncio
async def test_sql_generation_and_execution_are_separate(monkeypatch):
    generated_query = "SELECT id, name FROM customers"
    executor = FakeTool(
        "run_readonly_query",
        {"columns": ["id", "name"], "rows": [[1, "Ada"]]},
    )

    class FakeAgent:
        async def ainvoke(self, request):
            assert request["messages"][0]["content"] == "List customers"
            return {
                "messages": [
                    SimpleNamespace(content=generated_query)
                ]
            }

    monkeypatch.setattr(
        sql_agent,
        "build_sql_agent",
        lambda: _async_result(FakeAgent()),
    )
    monkeypatch.setattr(
        sql_agent,
        "build_sql_executor",
        lambda: _async_result(executor),
    )

    query = await sql_agent.generate_sql_query("List customers")
    assert query == generated_query
    assert executor.calls == []

    result = await sql_agent.execute_sql_query(query)
    assert executor.calls == [{"query": generated_query}]
    assert json.loads(result) == {
        "columns": ["id", "name"],
        "rows": [[1, "Ada"]],
    }


async def _async_result(value):
    return value
