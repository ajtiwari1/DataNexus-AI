from langgraph.types import interrupt

from app.graph.state import DataNexusState


def approval_node(state: DataNexusState) -> dict:
    decision = interrupt({
        "type": "sql_approval",
        "request_id": state["request_id"],
        "question": state["question"],
        "sql": state["sql_query"],
        "reason": state["approval_reason"],
    })

    if isinstance(decision, dict) and decision.get("approved") is True:
        return {
            "approval_status": "approved",
            "pending_approval": False,
        }

    return {
        "approval_status": "rejected",
        "pending_approval": False,
    }