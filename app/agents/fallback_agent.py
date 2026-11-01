import logging

logger = logging.getLogger(__name__)
from app.graph.state import DataNexusState


async def finalize_node(state: DataNexusState) -> dict:
    sql_result = state.get("sql_result", "")
    document_result = state.get("document_result", "")

    available_results = []

    if sql_result:
        available_results.append(
            f"### Database Results\n{sql_result}"
        )

    if document_result:
        available_results.append(
            f"### Document Results\n{document_result}"
        )

    if not available_results:
        return {
            "final_answer": (
                "I couldn't retrieve a reliable answer from the available "
                "data sources. Please try again."
            )
        }

    try:
        response = await get_llm().ainvoke(
            [
                (
                    "system",
                    "Combine the supplied database and document results. "
                    "Do not introduce facts that are not present in them.",
                ),
                (
                    "human",
                    "\n\n".join(available_results),
                ),
            ]
        )

        return {"final_answer": str(response.content)}

    except Exception:
        logger.exception("Final synthesis failed; using agent outputs")

        return {
            "final_answer": (
                "The results were retrieved, but final AI synthesis "
                "was unavailable.\n\n"
                + "\n\n".join(available_results)
            )
        }