import pytest
from app.agents.graph import create_analysis_graph, router_after_verification
from app.agents.state import AgentState


def test_graph_compilation():
    graph = create_analysis_graph()
    assert graph is not None
    # Verify graph contains our core nodes
    node_keys = graph.nodes.keys()
    assert "data_profiler_node" in node_keys
    assert "planner_node" in node_keys
    assert "analysis_node" in node_keys
    assert "visualization_node" in node_keys
    assert "insight_node" in node_keys
    assert "verification_node" in node_keys
    assert "replan_node" in node_keys
    assert "report_node" in node_keys


def test_router_after_verification_valid():
    state: AgentState = {
        "dataset_id": "test",
        "file_path": "test.csv",
        "user_query": "test",
        "profile": {},
        "profile_summary": "",
        "plan": [],
        "analysis_results": [],
        "visualizations": [],
        "insights": [],
        "verification": {"is_valid": True, "score": 95.0},
        "retry_count": 0,
        "max_retries": 2,
        "events": [],
        "final_report": None,
        "error": None,
    }
    decision = router_after_verification(state)
    assert decision == "report_node"


def test_router_after_verification_invalid():
    state: AgentState = {
        "dataset_id": "test",
        "file_path": "test.csv",
        "user_query": "test",
        "profile": {},
        "profile_summary": "",
        "plan": [],
        "analysis_results": [],
        "visualizations": [],
        "insights": [],
        "verification": {"is_valid": False, "score": 40.0},
        "retry_count": 0,
        "max_retries": 2,
        "events": [],
        "final_report": None,
        "error": None,
    }
    decision = router_after_verification(state)
    assert decision == "replan_node"
