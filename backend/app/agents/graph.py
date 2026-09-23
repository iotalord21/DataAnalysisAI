import time
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.data_agent import data_profiler_node
from app.agents.planner_agent import planner_node
from app.agents.analysis_agent import analysis_node
from app.agents.visualization_agent import visualization_agent_node
from app.agents.insight_agent import insight_agent_node
from app.agents.verification_agent import verification_agent_node
from app.agents.report_agent import report_agent_node


def replan_node(state: AgentState) -> Dict[str, Any]:
    """
    Re-plan Node:
    Increments retry count, preserves verification guidance, and re-routes
    into the analysis loop.
    """
    retry_count = state.get("retry_count", 0) + 1
    events = list(state.get("events", []))
    events.append({
        "stage": "Re-analyze",
        "agent": "Orchestrator",
        "message": f"Verification flagged discrepancies. Initiating Re-analysis cycle ({retry_count}/{state.get('max_retries', 2)})...",
        "timestamp": time.time(),
        "details": {"retry_count": retry_count},
    })
    return {
        "retry_count": retry_count,
        "events": events,
    }


def router_after_verification(state: AgentState) -> Literal["report_node", "replan_node"]:
    """
    Conditional routing based on Verification Agent assessment.
    """
    verification = state.get("verification")
    if not verification:
        return "report_node"

    if verification.get("is_valid", True):
        return "report_node"

    return "replan_node"


def create_analysis_graph():
    """
    Builds and compiles the complete LangGraph StateGraph:
    Plan → Act → Observe → Verify → Re-plan → Report
    """
    builder = StateGraph(AgentState)

    # Register Nodes
    builder.add_node("data_profiler_node", data_profiler_node)
    builder.add_node("planner_node", planner_node)
    builder.add_node("analysis_node", analysis_node)
    builder.add_node("visualization_node", visualization_agent_node)
    builder.add_node("insight_node", insight_agent_node)
    builder.add_node("verification_node", verification_agent_node)
    builder.add_node("replan_node", replan_node)
    builder.add_node("report_node", report_agent_node)

    # Define Linear Flow
    builder.add_edge(START, "data_profiler_node")
    builder.add_edge("data_profiler_node", "planner_node")
    builder.add_edge("planner_node", "analysis_node")
    builder.add_edge("analysis_node", "visualization_node")
    builder.add_edge("visualization_node", "insight_node")
    builder.add_edge("insight_node", "verification_node")

    # Define Conditional Verification Loop
    builder.add_conditional_edges(
        "verification_node",
        router_after_verification,
        {
            "report_node": "report_node",
            "replan_node": "replan_node",
        },
    )

    # Connect Re-plan back to Analysis
    builder.add_edge("replan_node", "analysis_node")

    # Connect Report to End
    builder.add_edge("report_node", END)

    return builder.compile()
