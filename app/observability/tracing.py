
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
) -> dict:
    client = get_langfuse_client()

    if client is None:
        return await workflow.ainvoke({"question": question})

    try:
        from langfuse.langchain import CallbackHandler

        handler = CallbackHandler()

        with client.start_as_current_observation(
            as_type="span",
            name="datanexus-chat",
            input={"question": question},
        ) as span:
            result = await workflow.ainvoke(
                {"question": question},
                config={"callbacks": [handler]},
            )

            span.update(
                output={
                    "answer": result.get("final_answer", ""),
                    "intent": result.get("intent", "unknown"),
                    "errors": result.get("errors", []),
                }
            )

            return result

    except Exception:
        logger.exception("Tracing integration failed; running workflow without tracing")
        return await workflow.ainvoke({"question": question})
