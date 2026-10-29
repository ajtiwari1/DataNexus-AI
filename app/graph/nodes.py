
import logging
import os

from langchain_openai import ChatOpenAI

from app.agents.sql_agent import ask_sql_agent
from app.agents.rag_agent import rag_node
from app.graph.state import DataNexusState


def get_llm():
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.getenv(
            "OPENAI_BASE_URL",
            "https://openrouter.ai/api/v1",
        ),
        temperature=0,
    )


async def supervisor_node(state: DataNexusState) -> dict:
    response = await get_llm().ainvoke([
        (
            "system",
            """
            Route the question to exactly one category:
            sql       - structured database questions
            documents - questions answered by documents
            both      - requires both database and document evidence
            general   - general questions unrelated to either source

            Return only the category word.
            Do not answer the question.
            """,
        ),
        ("human", state["question"]),
    ])

    intent = str(response.content).strip().lower()
    if intent not in {"sql", "documents", "both", "general"}:
        intent = "general"

    return {"intent": intent}


async def sql_node(state: DataNexusState) -> dict:
    try:
        result = await ask_sql_agent(state["question"])
        return {"sql_result": result}
    except Exception as exc:
        logging.exception("SQL agent failed")
        return {
            "sql_result": "",
            "errors": [f"SQL agent failed: {type(exc).__name__}"],
        }


async def general_node(state: DataNexusState) -> dict:
    response = await get_llm().ainvoke([
        (
            "system",
            "Answer general questions concisely. Do not claim to have "
            "queried the database or searched documents.",
        ),
        ("human", state["question"]),
    ])
    return {"final_answer": str(response.content)}


async def finalize_node(state: DataNexusState) -> dict:
    sql_result = state.get("sql_result", "")
    document_result = state.get("document_result", "")
    intent = state.get("intent", "general")
    errors = state.get("errors", [])

    # Return the specialist's answer directly for single-source requests.
    if intent == "sql":
        return {
            "final_answer": sql_result or
            "The SQL agent could not produce a result."
        }

    if intent == "documents":
        return {
            "final_answer": document_result or
            "No document-based answer could be produced."
        }

    # For dual-source questions, preserve available evidence if one agent fails.
    if not sql_result and not document_result:
        return {
            "final_answer": "Neither specialist returned usable evidence."
        }

    if not sql_result or not document_result:
        available = sql_result or document_result
        return {
            "final_answer": (
                f"Partial result (one specialist failed):\n{available}"
            )
        }

    response = await get_llm().ainvoke([
        (
            "system",
            """
            Combine the SQL result and document result into one answer.
            Keep database facts and document claims distinguishable.
            Do not invent facts or claim that sources agree when they differ.
            If evidence conflicts, explain the conflict.
            """,
        ),
        (
            "human",
            f"Question: {state['question']}\n\n"
            f"SQL evidence:\n{sql_result}\n\n"
            f"Document evidence:\n{document_result}",
        ),
    ])

    answer = str(response.content)
    if errors:
        answer += "\n\nNote: One or more agents reported an error."

    return {"final_answer": answer}
