
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    finalize_node,
    general_node,
    sql_node,
    supervisor_node,
)
from app.agents.rag_agent import rag_node
from app.graph.state import DataNexusState


def route_by_intent(state: DataNexusState):
    intent = state.get("intent", "general")

    if intent == "sql":
        return "sql_agent"

    if intent == "documents":
        return "rag_agent"

    if intent == "both":
        # LangGraph fans out to both nodes in the same graph step.
        return ["sql_agent", "rag_agent"]

    return "general"


def build_workflow():
    graph = StateGraph(DataNexusState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("sql_agent", sql_node)
    graph.add_node("rag_agent", rag_node)
    graph.add_node("general", general_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "supervisor")

    # Dynamic routing allows one specialist or parallel specialists.
    graph.add_conditional_edges(
        "supervisor",
        route_by_intent,
    )

    graph.add_edge("sql_agent", "finalize")
    graph.add_edge("rag_agent", "finalize")
    graph.add_edge("finalize", END)
    graph.add_edge("general", END)

    return graph.compile()


workflow = build_workflow()
