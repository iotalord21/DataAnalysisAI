import time
from typing import Dict, Any
from app.agents.state import AgentState
from app.tools.data_profiler import DataProfiler


def data_profiler_node(state: AgentState) -> Dict[str, Any]:
    """
    Data Agent:
    Loads the uploaded dataset, performs deep statistical profiling,
    detects anomalies/missingness, and summarizes key characteristics.
    """
    file_path = state["file_path"]
    profiler = DataProfiler()

    profile = profiler.profile_file(file_path)
    profile_summary = profiler.format_for_prompt(profile)

    event = {
        "stage": "Data Profiling",
        "agent": "Data Agent",
        "message": f"Successfully profiled dataset '{profile.get('filename')}' ({profile['total_rows']} rows, {profile['total_columns']} columns).",
        "timestamp": time.time(),
        "details": {
            "rows": profile["total_rows"],
            "columns": profile["total_columns"],
            "numeric_columns": profile["numeric_columns"],
            "categorical_columns": profile["categorical_columns"],
            "duplicates": profile["duplicate_rows"],
        },
    }

    current_events = list(state.get("events", []))
    current_events.append(event)

    return {
        "profile": profile,
        "profile_summary": profile_summary,
        "events": current_events,
    }
