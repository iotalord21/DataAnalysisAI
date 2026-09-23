import json
import time
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.agents.llm_factory import get_llm
from app.tools.python_repl import PythonReplTool


ANALYSIS_SYSTEM_PROMPT = """You are an expert Data Science Engineer writing Python code for analytical computations.
The target dataset is ALREADY loaded in the environment as the pandas DataFrame `df`.

Requirements:
1. Write clean, idiomatic Python using `pandas`, `numpy`, `scipy.stats`, or `statsmodels`.
2. Assign your primary findings/metrics to the global variable `result` as a dictionary, for example:
   result = {
       "metric_name": value,
       "summary_table": df.groupby('col')['metric'].mean().to_dict()
   }
3. Also use `print()` statements to print readable formatted summaries of your calculations.
4. DO NOT import os, sys, subprocess, requests, or builtins (forbidden for security).
5. Only return the raw executable Python code inside a ```python ``` codeblock.
"""


def _generate_code_for_step(step: Dict[str, Any], profile_summary: str, previous_error: str = "") -> str:
    user_prompt = f"""
Dataset Details:
{profile_summary}

Task:
Title: {step['title']}
Analysis Type: {step['analysis_type']}
Description: {step['description']}
Hypothesis: {step.get('hypothesis', 'N/A')}
"""
    if previous_error:
        user_prompt += f"""
PREVIOUS CODE ATTEMPT FAILED WITH ERROR:
{previous_error}
Please diagnose and fix this error in your revised code. Double check column names and data types!
"""

    llm = get_llm(temperature=0.1)
    response = llm.invoke([
        SystemMessage(content=ANALYSIS_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])
    raw_text = response.content.strip()

    # Extract code from code block
    match = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", raw_text)
    if match:
        return match.group(1).strip()
    return raw_text


def _fallback_code_for_step(step: Dict[str, Any], numeric_cols: List[str], cat_cols: List[str]) -> str:
    analysis_type = step.get("analysis_type", "statistics")
    if analysis_type == "correlation" and len(numeric_cols) >= 2:
        return f"""
corr_matrix = df[{numeric_cols[:4]}].corr().round(4).to_dict()
print("Correlation Matrix:", corr_matrix)
result = {{"correlation_matrix": corr_matrix}}
"""
    elif analysis_type == "segmentation" and cat_cols and numeric_cols:
        cat = cat_cols[0]
        num = numeric_cols[0]
        return f"""
seg = df.groupby('{cat}')['{num}'].agg(['count', 'mean', 'std', 'median']).round(2)
print("Segmentation Table:")
print(seg)
result = {{"segmentation": seg.to_dict(orient='index')}}
"""
    elif analysis_type == "outliers" and numeric_cols:
        num = numeric_cols[0]
        return f"""
q1 = df['{num}'].quantile(0.25)
q3 = df['{num}'].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr
outliers = df[(df['{num}'] < lower) | (df['{num}'] > upper)]
print(f"Detected {{len(outliers)}} outliers in {num} (IQR range [{{lower:.2f}}, {{upper:.2f}}])")
result = {{
    "column": "{num}",
    "outliers_count": len(outliers),
    "lower_bound": float(lower),
    "upper_bound": float(upper)
}}
"""
    else:
        # Default statistics
        cols = numeric_cols[:3] if numeric_cols else list(df.columns[:3])
        return f"""
desc = df[{cols}].describe().round(3)
print("Summary Statistics:")
print(desc)
result = {{"summary_statistics": desc.to_dict()}}
"""


def analysis_node(state: AgentState) -> Dict[str, Any]:
    """
    Analysis Agent:
    Executes each planned analytical step by generating Python code,
    running it inside the isolated subprocess sandbox, observing outputs,
    and self-correcting if runtime errors occur.
    """
    plan = state.get("plan", [])
    file_path = state["file_path"]
    profile_summary = state.get("profile_summary", "")
    profile = state.get("profile", {})
    numeric_cols = profile.get("numeric_columns", [])
    cat_cols = profile.get("categorical_columns", [])

    repl = PythonReplTool()
    analysis_results = []
    events = list(state.get("events", []))

    for step in plan:
        step_id = step["id"]
        step_title = step["title"]
        print(f"[Analysis Agent] Executing {step_id}: {step_title}...")

        # Add event for start of step
        events.append({
            "stage": "Execute Required Analyses",
            "agent": "Analysis Agent",
            "message": f"Running: {step_title}...",
            "timestamp": time.time(),
            "details": {"step_id": step_id, "status": "running"},
        })

        success = False
        exec_res = None
        attempt_error = ""

        # Up to 2 execution attempts (self-correction)
        for attempt in range(2):
            try:
                code = _generate_code_for_step(step, profile_summary, previous_error=attempt_error)
            except Exception as e:
                print(f"[Analysis Agent] Code generation failed, using fallback: {e}")
                code = _fallback_code_for_step(step, numeric_cols, cat_cols)

            exec_res = repl.execute(code, file_path)

            if exec_res.success:
                success = True
                break
            else:
                attempt_error = exec_res.error or exec_res.stderr or "Unknown execution error"
                print(f"[Analysis Agent] Attempt {attempt+1} failed with error: {attempt_error}. Retrying with self-correction...")

        # If still failed after retries, use safe deterministic fallback
        if not success:
            fallback_code = _fallback_code_for_step(step, numeric_cols, cat_cols)
            exec_res = repl.execute(fallback_code, file_path)
            success = exec_res.success

        result_item = {
            "step_id": step_id,
            "code": exec_res.code_executed,
            "success": exec_res.success,
            "stdout": exec_res.stdout,
            "error": exec_res.error,
            "result_data": exec_res.result_data,
            "execution_time_ms": exec_res.execution_time_ms,
        }
        analysis_results.append(result_item)

        status_msg = "Completed successfully" if exec_res.success else f"Encountered error: {exec_res.error}"
        events.append({
            "stage": "Execute Required Analyses",
            "agent": "Analysis Agent",
            "message": f"Step '{step_title}': {status_msg} ({exec_res.execution_time_ms}ms).",
            "timestamp": time.time(),
            "details": {"step_id": step_id, "success": exec_res.success, "stdout": exec_res.stdout[:500]},
        })

    return {
        "analysis_results": analysis_results,
        "events": events,
    }
