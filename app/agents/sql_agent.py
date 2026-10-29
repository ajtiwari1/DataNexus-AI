
import os

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


async def build_sql_agent():
    # 1. Connect to the MCP server
    client = MultiServerMCPClient(
        {
            "postgres": {
                "transport": "streamable_http",
                "url": os.getenv(
                    "MCP_URL",
                    "http://mcp:8001/mcp",
                ),
            }
        }
    )

    # 2. Discover tools dynamically from MCP
    tools = await client.get_tools()

    # 3. Configure the LLM
    llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv(
        "OPENAI_BASE_URL",
        "https://openrouter.ai/api/v1",
    ),
    temperature=0,
    )
    

    # 4. Create the LangGraph tool-calling agent
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt="""
        You are the SQL specialist for DataNexus AI.

        Rules:
        - Use MCP tools to inspect the database schema.
        - Use only the available database tools.
        - Execute read-only queries only.
        - Never invent database results.
        - If the data is insufficient, explain what is missing.
        """,
    )

    return agent


async def ask_sql_agent(question: str) -> str:
    agent = await build_sql_agent()

    result = await agent.ainvoke(
        {
            "messages": [
                {"role": "user", "content": question}
            ]
        }
    )

    return result["messages"][-1].content
