from langgraph.types import interrupt


def approval_node(state):
    decision = interrupt({
        "type": "sql_approval",
        "question": state["question"],
        "sql": state["generated_sql"],
        "reason": state["approval_reason"],
    })

    if decision.get("approved") is True:
        return {
            "approval_status": "approved"
        }

    return {
        "approval_status": "rejected"
    }