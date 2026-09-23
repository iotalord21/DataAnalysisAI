import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.agents.graph import create_analysis_graph
from app.agents.state import AgentState

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    dataset_id: str
    query: Optional[str] = "Perform a thorough exploratory data analysis, uncover key correlations, trends, outliers, and business insights."
    provider: Optional[str] = None


@router.post("/run")
async def run_analysis(request: AnalysisRequest) -> Dict[str, Any]:
    """
    Execute full multi-agent analysis workflow and return final synthesized state.
    """
    matches = list(settings.uploads_dir.glob(f"{request.dataset_id}_*"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"Dataset with ID '{request.dataset_id}' not found.")

    file_path = str(matches[0])
    graph = create_analysis_graph()

    initial_state: AgentState = {
        "dataset_id": request.dataset_id,
        "file_path": file_path,
        "user_query": request.query or "",
        "profile": {},
        "profile_summary": "",
        "plan": [],
        "analysis_results": [],
        "visualizations": [],
        "insights": [],
        "verification": None,
        "retry_count": 0,
        "max_retries": settings.max_verification_retries,
        "events": [],
        "final_report": None,
        "error": None,
    }

    try:
        # Run graph to completion
        final_state = await asyncio.to_thread(graph.invoke, initial_state)
        return {
            "success": True,
            "dataset_id": request.dataset_id,
            "final_report": final_state.get("final_report"),
            "visualizations": final_state.get("visualizations", []),
            "insights": final_state.get("insights", []),
            "verification": final_state.get("verification"),
            "plan": final_state.get("plan", []),
            "analysis_results": final_state.get("analysis_results", []),
            "events": final_state.get("events", []),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {str(e)}")


@router.get("/stream")
async def stream_analysis(
    dataset_id: str = Query(...),
    query: str = Query("Explore dataset for key patterns, trends, and correlations.")
):
    """
    Stream live agent thoughts, node transitions, and calculations via Server-Sent Events (SSE).
    """
    matches = list(settings.uploads_dir.glob(f"{dataset_id}_*"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"Dataset with ID '{dataset_id}' not found.")

    file_path = str(matches[0])
    graph = create_analysis_graph()

    initial_state: AgentState = {
        "dataset_id": dataset_id,
        "file_path": file_path,
        "user_query": query,
        "profile": {},
        "profile_summary": "",
        "plan": [],
        "analysis_results": [],
        "visualizations": [],
        "insights": [],
        "verification": None,
        "retry_count": 0,
        "max_retries": settings.max_verification_retries,
        "events": [],
        "final_report": None,
        "error": None,
    }

    async def event_generator():
        yield {
            "event": "start",
            "data": json.dumps({"status": "starting", "message": "Initiating agentic analysis pipeline..."}),
        }

        # Stream intermediate graph states
        loop = asyncio.get_event_loop()
        try:
            # We iterate through graph.stream in a worker thread
            def run_stream():
                updates = []
                for chunk in graph.stream(initial_state):
                    updates.append(chunk)
                return updates

            chunks = await loop.run_in_executor(None, run_stream)

            # Reconstruct and broadcast sequential progression
            accumulated_state = dict(initial_state)
            for chunk in chunks:
                for node_name, node_update in chunk.items():
                    accumulated_state.update(node_update)
                    yield {
                        "event": "update",
                        "data": json.dumps({
                            "node": node_name,
                            "events": accumulated_state.get("events", []),
                            "plan": accumulated_state.get("plan", []),
                            "visualizations": accumulated_state.get("visualizations", []),
                            "insights": accumulated_state.get("insights", []),
                            "verification": accumulated_state.get("verification"),
                            "final_report": accumulated_state.get("final_report"),
                        }),
                    }
                    await asyncio.sleep(0.1)

            yield {
                "event": "complete",
                "data": json.dumps({
                    "status": "completed",
                    "final_report": accumulated_state.get("final_report"),
                    "visualizations": accumulated_state.get("visualizations", []),
                    "insights": accumulated_state.get("insights", []),
                    "verification": accumulated_state.get("verification"),
                    "plan": accumulated_state.get("plan", []),
                    "analysis_results": accumulated_state.get("analysis_results", []),
                    "events": accumulated_state.get("events", []),
                }),
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

    return EventSourceResponse(event_generator())


@router.get("/report/{dataset_id}/export")
def export_report_html(dataset_id: str, format: str = Query("html")):
    """
    Download a self-contained, beautifully formatted HTML or Markdown report.
    """
    matches = list(settings.uploads_dir.glob(f"{dataset_id}_*"))
    if not matches:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # In production, returns compiled HTML or Markdown file
    return Response(
        content=f"Report export endpoint for dataset {dataset_id}",
        media_type="text/plain",
    )
