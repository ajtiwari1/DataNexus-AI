
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    finalize_node,
    general_node,
    sql_execution_node,
    sql_generation_node,
    supervisor_node,
)
from app.agents.rag_agent import rag_node
from app.graph.state import DataNexusState


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
    return "sql_execution" if state.get("sql_query") else "finalize"


def build_workflow():
    graph = StateGraph(DataNexusState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("sql_generation", sql_generation_node)
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
            "sql_execution": "sql_execution",
            "finalize": "finalize",
        },
    )
    graph.add_edge("sql_execution", "finalize")
    graph.add_edge("rag_agent", "finalize")
    graph.add_edge("finalize", END)
    graph.add_edge("general", END)

    return graph.compile()


workflow = build_workflow()
