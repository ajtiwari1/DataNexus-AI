
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.graph.nodes import (
    finalize_node,
    general_node,
    sql_execution_node,
    sql_generation_node,
    sql_validation_node,
    supervisor_node,
)
from app.agents.rag_agent import rag_node
from app.graph.state import DataNexusState
from app.security.approval import approval_node


def route_by_intent(state: DataNexusState):
    intent = state.get("intent", "general")

    if intent == "sql":
        return "sql_generation"

    if intent == "documents":
        return "rag_agent"

    if intent == "both":
        # LangGraph fans out to both nodes in the same graph step.
        return ["sql_generation", "rag_agent"]

    return "general"


def route_after_sql_generation(state: DataNexusState) -> str:
    return "sql_validation" if state.get("sql_query") else "finalize"


def route_after_sql_validation(state: DataNexusState) -> str:
    return "sql_approval" if state.get("pending_approval") else "finalize"


def route_after_approval(state: DataNexusState) -> str:
    return (
        "sql_execution"
        if state.get("approval_status") == "approved"
        else "finalize"
    )


def build_workflow(checkpointer=None):
    graph = StateGraph(DataNexusState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("sql_generation", sql_generation_node)
    graph.add_node("sql_validation", sql_validation_node)
    graph.add_node("sql_approval", approval_node)
    graph.add_node("sql_execution", sql_execution_node)
    graph.add_node("rag_agent", rag_node)
    graph.add_node("general", general_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "supervisor")

    # Dynamic routing allows one specialist or parallel specialists.
    graph.add_conditional_edges(
        "supervisor",
        route_by_intent,
    )

    graph.add_conditional_edges(
        "sql_generation",
        route_after_sql_generation,
        {
            "sql_validation": "sql_validation",
            "finalize": "finalize",
        },
    )
    graph.add_conditional_edges(
        "sql_validation",
        route_after_sql_validation,
        {
            "sql_approval": "sql_approval",
            "finalize": "finalize",
        },
    )
    graph.add_conditional_edges(
        "sql_approval",
        route_after_approval,
        {
            "sql_execution": "sql_execution",
            "finalize": "finalize",
        },
    )
    graph.add_edge("sql_execution", "finalize")
    graph.add_edge("rag_agent", "finalize")
    graph.add_edge("finalize", END)
    graph.add_edge("general", END)

    return graph.compile(checkpointer=checkpointer or MemorySaver())


workflow = build_workflow()
