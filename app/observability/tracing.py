
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def langfuse_enabled() -> bool:
    return (
        os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
        and bool(os.getenv("LANGFUSE_PUBLIC_KEY"))
        and bool(os.getenv("LANGFUSE_SECRET_KEY"))
    )


def get_langfuse_client():
    if not langfuse_enabled():
        return None

    try:
        from langfuse import get_client
        return get_client()
    except Exception:
        logger.exception("Could not initialize Langfuse")
        return None


async def run_traced_workflow(
    workflow: Any,
    question: str,
    config: dict | None = None,
    state: dict | None = None,
) -> dict:
    client = get_langfuse_client()
    workflow_input = state or {"question": question}

    if client is None:
        return await workflow.ainvoke(
            workflow_input,
            config=config,
        )

    try:
        from langfuse.langchain import CallbackHandler

        handler = CallbackHandler()
    except Exception:
        logger.exception("Could not initialize Langfuse tracing")
        return await workflow.ainvoke(
            workflow_input,
            config=config,
        )

    run_config = dict(config or {})
    run_config["callbacks"] = [
        *run_config.get("callbacks", []),
        handler,
    ]

    with client.start_as_current_observation(
        as_type="span",
        name="datanexus-chat",
        input={"question": question},
    ) as span:
        result = await workflow.ainvoke(
            workflow_input,
            config=run_config,
        )

        span.update(
            output={
                "answer": result.get("final_answer", ""),
                "intent": result.get("intent", "unknown"),
                "errors": result.get("errors", []),
                "approval_status": result.get("approval_status"),
            }
        )

        return result
